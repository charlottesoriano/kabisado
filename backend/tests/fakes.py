"""Recording fakes for the Storage and JobQueue interfaces."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.errors import AlreadyProcessing
from app.services.storage import SignedUpload, StoredObject


@dataclass
class FakeStorage:
    objects: dict[str, bytes] = field(default_factory=dict)
    calls: list[tuple[str, Any]] = field(default_factory=list)
    fail_with: Exception | None = None

    def _call(self, name: str, arg: Any) -> None:
        self.calls.append((name, arg))
        if self.fail_with is not None:
            raise self.fail_with

    def put(self, path: str, data: bytes) -> None:
        self.objects[path] = data

    async def create_signed_upload_url(self, path: str) -> SignedUpload:
        self._call("create_signed_upload_url", path)
        return SignedUpload(
            url=f"https://storage.test/object/upload/sign/uploads/{path}?token=t",
            path=path,
            token="t",  # noqa: S106 (fake)
            expires_at=datetime.now(UTC) + timedelta(hours=2),
        )

    async def create_signed_download_url(self, path: str, expires_in: int) -> str:
        self._call("create_signed_download_url", path)
        return f"https://storage.test/object/sign/uploads/{path}?token=d"

    async def stat(self, path: str) -> StoredObject | None:
        self._call("stat", path)
        data = self.objects.get(path)
        return None if data is None else StoredObject(path, len(data), "application/pdf")

    async def download(self, path: str) -> bytes:
        self._call("download", path)
        return self.objects[path]

    async def delete(self, paths: list[str]) -> None:
        self._call("delete", list(paths))
        for p in paths:
            self.objects.pop(p, None)

    async def delete_prefix(self, prefix: str) -> int:
        self._call("delete_prefix", prefix)
        doomed = [p for p in self.objects if p.startswith(prefix.rstrip("/") + "/")]
        for p in doomed:
            del self.objects[p]
        return len(doomed)

    async def aclose(self) -> None:
        pass

    def names(self) -> list[str]:
        return [name for name, _ in self.calls]


@dataclass
class FakeQueue:
    jobs: list[UUID] = field(default_factory=list)
    waiting: set[UUID] = field(default_factory=set)
    discarded: list[UUID] = field(default_factory=list)
    fail_with: Exception | None = None

    async def enqueue_generation(self, document_id: UUID) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        if document_id in self.waiting:
            raise AlreadyProcessing(context={"document_id": document_id})
        self.waiting.add(document_id)
        self.jobs.append(document_id)

    async def discard_waiting(self, document_id: UUID) -> None:
        self.discarded.append(document_id)
        self.waiting.discard(document_id)

    async def aclose(self) -> None:
        pass
