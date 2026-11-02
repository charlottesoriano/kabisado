"""Enqueueing background jobs from the API.

Routes depend on the ``JobQueue`` protocol (``get_job_queue``); tests swap in a recording fake.
The real queue defers the Procrastinate task with ``queueing_lock = document id``, so a document
can have at most one waiting job (a second enqueue is ``already_processing``).

Routes commit the document first and enqueue afterwards. If enqueueing fails they call
``discard_waiting`` (so no stale queueing lock can block a later Retry) and mark the document
``failed`` with ``enqueue_failed``.
"""

import asyncio
from typing import Protocol
from uuid import UUID

import structlog
from procrastinate import App
from procrastinate.exceptions import AlreadyEnqueued

from app.errors import AlreadyProcessing, AppError, guard
from app.jobs.app import app as procrastinate_app
from app.jobs.generate_document import generate_document

log = structlog.get_logger("app.jobs")


class JobQueue(Protocol):
    async def enqueue_generation(self, document_id: UUID) -> None:
        """Queue ``generate_document``; raise ``AlreadyProcessing`` if one is waiting."""
        ...

    async def discard_waiting(self, document_id: UUID) -> None:
        """Best effort: delete any not-yet-started job for the document (frees its lock)."""
        ...

    async def aclose(self) -> None: ...


class ProcrastinateQueue:
    def __init__(self, app: App = procrastinate_app) -> None:
        self._app = app
        self._open = False
        self._lock = asyncio.Lock()

    async def _ensure_open(self) -> None:
        async with self._lock:
            if not self._open:
                with guard("jobs.open"):
                    await self._app.open_async()
                self._open = True

    async def enqueue_generation(self, document_id: UUID) -> None:
        await self._ensure_open()
        try:
            with guard("jobs.enqueue_generation", document_id=document_id):
                deferrer = self._app.configure_task(
                    generate_document.name, queueing_lock=str(document_id)
                )
                await deferrer.defer_async(document_id=str(document_id))
        except AppError as err:
            if isinstance(err.__cause__, AlreadyEnqueued):
                raise AlreadyProcessing(
                    operation="jobs.enqueue_generation", context={"document_id": document_id}
                ) from err.__cause__
            raise

    async def discard_waiting(self, document_id: UUID) -> None:
        try:
            await self._ensure_open()
            manager = self._app.job_manager
            waiting = await manager.list_jobs_async(queueing_lock=str(document_id), status="todo")
            for job in waiting:
                if job.id is not None:
                    await manager.cancel_job_by_id_async(job.id, delete_job=True)
        except Exception as exc:  # the queue may be the thing that's down
            log.warning(
                "discard_waiting_failed",
                document_id=str(document_id),
                error_type=type(exc).__name__,
            )

    async def aclose(self) -> None:
        if self._open:
            await self._app.close_async()
            self._open = False


_queue: ProcrastinateQueue | None = None


def get_job_queue() -> JobQueue:
    """FastAPI dependency: the process-wide job queue."""
    global _queue
    if _queue is None:
        _queue = ProcrastinateQueue()
    return _queue


async def close_job_queue() -> None:
    global _queue
    if _queue is not None:
        await _queue.aclose()
    _queue = None
