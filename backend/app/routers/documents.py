"""Documents (decks): create + signed upload URL, process, pasted text, list, detail,
rename, retry, delete, show source chunk.

Every query is scoped to the verified user id; another user's document is 404.
"""

from collections import defaultdict
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Response, status
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentProfile, CurrentUserId
from app.config import get_settings
from app.db import models
from app.db.models import CardType, DocumentStatus, SourceType
from app.db.session import SessionDep
from app.errors import (
    AlreadyProcessing,
    AppError,
    EnqueueFailed,
    FileTooLarge,
    InvalidFile,
    InvalidState,
    NotFound,
    PageLimitExceeded,
    UploadMissing,
    error_responses,
    guard,
)
from app.jobs.queue import JobQueue, get_job_queue
from app.services.extraction import count_pages, looks_like_pdf
from app.services.ratelimit import default_rate_limit, take_upload_slot
from app.services.stats import MASTERED_INTERVAL_DAYS, mastery_pct, today_bounds
from app.services.storage import Storage, get_storage, pdf_path

router = APIRouter(tags=["documents"], dependencies=[Depends(default_rate_limit)])

StorageDep = Annotated[Storage, Depends(get_storage)]
QueueDep = Annotated[JobQueue, Depends(get_job_queue)]

ALL_KINDS: list[CardType] = ["flashcard", "mcq", "problem"]

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
# Leading/trailing whitespace is stripped before the length check and not stored, so
# whitespace can't pad notes past the 200-character minimum.
NotesText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=200, max_length=100_000)
]

# Failures caused by the file itself: retrying can't help, the student must upload a new file.
NOT_RETRYABLE = {
    PageLimitExceeded.code: (
        "This PDF has too many pages to turn into a deck. Split it into smaller parts and "
        "upload them as new decks."
    ),
    InvalidFile.code: (
        "This file couldn't be read as a PDF. Please upload a new file as a new deck."
    ),
}


def _unique_kinds(v: list[CardType]) -> list[CardType]:
    if len(set(v)) != len(v):
        raise ValueError("generate_kinds must not repeat a kind")
    return v


GenerateKinds = Annotated[
    list[CardType],
    Field(min_length=1, max_length=3, description="What to generate; default all three"),
    AfterValidator(_unique_kinds),
]


# Models -----------------------------------------------------------------------------------------
class DocumentProgress(BaseModel):
    done: int = Field(description="Chunks finished")
    total: int = Field(description="Chunks to generate (0 until chunking is done)")


class CardCounts(BaseModel):
    """Unflagged cards per type."""

    flashcard: int = 0
    mcq: int = 0
    problem: int = 0


class Document(BaseModel):
    id: UUID
    title: str
    source_type: SourceType
    status: DocumentStatus
    error_code: str | None = Field(
        description="Why generation failed, e.g. scanned_pdf, page_limit_exceeded"
    )
    page_count: int | None
    generate_kinds: list[CardType]
    progress: DocumentProgress
    card_counts: CardCounts
    due_count: int = Field(description="Flashcards due by the end of today (user's time zone)")
    mastery_pct: int = Field(description="Share of cards with an interval of 21+ days, 0-100")
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    items: list[Document]


class UploadTarget(BaseModel):
    """Where the client PUTs the PDF (Supabase signed upload URL)."""

    url: str
    path: str
    token: str
    expires_at: datetime


class CreateDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    filename: str = Field(min_length=1, max_length=255, description="Must end in .pdf")
    size_bytes: int = Field(gt=0, description="File size; at most MAX_UPLOAD_MB MiB")
    generate_kinds: GenerateKinds = ALL_KINDS


class CreateDocumentResponse(BaseModel):
    document: Document
    upload: UploadTarget


class CreateTextDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    text: NotesText
    generate_kinds: GenerateKinds = ALL_KINDS


class RenameDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title


class Chunk(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    idx: int
    heading: str | None
    content: str
    page_start: int
    page_end: int


# Helpers ----------------------------------------------------------------------------------------
async def owned_document(
    session: AsyncSession, user_id: str, document_id: UUID, *, for_update: bool = False
) -> models.Document:
    stmt = select(models.Document).where(
        models.Document.id == document_id, models.Document.user_id == user_id
    )
    if for_update:
        stmt = stmt.with_for_update()
    with guard("db.get_document", document_id=document_id):
        doc = (await session.execute(stmt)).scalar_one_or_none()
    if doc is None:
        raise NotFound(context={"document_id": document_id})
    return doc


async def _user_timezone(session: AsyncSession, user_id: str) -> str | None:
    stmt = select(models.Profile.timezone).where(models.Profile.id == user_id)
    with guard("db.get_timezone", user_id=user_id):
        return (await session.execute(stmt)).scalar_one_or_none()


def _document_out(doc: models.Document, stats: dict[str, Any] | None = None) -> Document:
    stats = stats or {}
    return Document(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        status=doc.status,
        error_code=doc.error_code,
        page_count=doc.page_count,
        generate_kinds=list(doc.generate_kinds),
        progress=DocumentProgress(done=doc.progress_done, total=doc.progress_total),
        card_counts=CardCounts(**stats.get("counts", {})),
        due_count=stats.get("due", 0),
        mastery_pct=mastery_pct(stats.get("mastered", 0), stats.get("states", 0)),
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def documents_out(
    session: AsyncSession, user_id: str, docs: list[models.Document]
) -> list[Document]:
    """Documents with card counts, due count and mastery (two grouped queries)."""
    if not docs:
        return []
    ids = [d.id for d in docs]
    stats: dict[UUID, dict[str, Any]] = defaultdict(lambda: {"counts": {}})
    card, state = models.Card, models.CardState

    counts = (
        select(card.document_id, card.type, func.count())
        .where(card.document_id.in_(ids), card.flagged.is_(False))
        .group_by(card.document_id, card.type)
    )
    _, end_of_today = today_bounds(await _user_timezone(session, user_id))
    states = (
        select(
            card.document_id,
            func.count().filter(and_(state.due_at < end_of_today, card.type == "flashcard")),
            func.count().filter(state.interval_days >= MASTERED_INTERVAL_DAYS),
            func.count(),
        )
        .select_from(state)
        .join(card, card.id == state.card_id)
        .where(state.user_id == user_id, card.document_id.in_(ids), card.flagged.is_(False))
        .group_by(card.document_id)
    )
    with guard("db.document_stats", user_id=user_id):
        for doc_id, card_type, n in (await session.execute(counts)).all():
            stats[doc_id]["counts"][card_type] = n
        for doc_id, due, mastered, total in (await session.execute(states)).all():
            stats[doc_id].update(due=due, mastered=mastered, states=total)
    return [_document_out(d, stats.get(d.id)) for d in docs]


async def _commit(session: AsyncSession, **ids: Any) -> None:
    with guard("db.commit", **ids):
        await session.commit()


async def _enqueue_committed(session: AsyncSession, queue: JobQueue, doc: models.Document) -> None:
    """Queue generation for a document whose state is already committed.

    - A job already waiting (``already_processing``): the committed state is right; re-raise.
    - Any other failure: drop any half-created job (no stale queueing lock), mark the deck
      ``failed`` / ``enqueue_failed`` so Retry works, and answer 503 ``enqueue_failed``.
    """
    document_id = doc.id
    try:
        await queue.enqueue_generation(document_id)
    except AlreadyProcessing:
        raise
    except Exception as exc:
        await queue.discard_waiting(document_id)
        doc.status = "failed"
        doc.error_code = EnqueueFailed.code
        await _commit(session, document_id=document_id)
        cause = exc if not isinstance(exc, AppError) else (exc.__cause__ or exc)
        raise EnqueueFailed(
            operation="jobs.enqueue_generation", context={"document_id": document_id}
        ) from cause


# Routes -----------------------------------------------------------------------------------------
@router.post(
    "/documents",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateDocumentResponse,
    responses=error_responses(401, 422, 429, 502, 503),
)
async def create_document(
    body: CreateDocumentRequest, profile: CurrentProfile, session: SessionDep, storage: StorageDep
) -> CreateDocumentResponse:
    """Create a PDF deck (`queued`) and return a signed URL to upload the file to. Call
    `POST /documents/{id}/process` after the upload finishes."""
    settings = get_settings()
    if not body.filename.lower().endswith(".pdf"):
        raise InvalidFile(context={"extension": body.filename.rsplit(".", 1)[-1][:10]})
    if body.size_bytes > settings.max_upload_bytes:
        raise FileTooLarge(
            f"This PDF is larger than {settings.max_upload_mb} MB. Please choose a smaller file.",
            context={"size_bytes": body.size_bytes},
        )
    await take_upload_slot(session, profile.id)

    document_id = uuid4()
    path = pdf_path(profile.id, document_id)
    doc = models.Document(
        id=document_id,
        user_id=profile.id,
        title=body.title,
        source_type="pdf",
        file_path=path,
        generate_kinds=list(body.generate_kinds),
    )
    session.add(doc)
    with guard("db.create_document", document_id=document_id):
        await session.flush()
    upload = await storage.create_signed_upload_url(path)
    await _commit(session, document_id=document_id)
    await session.refresh(doc)
    return CreateDocumentResponse(
        document=_document_out(doc),
        upload=UploadTarget(
            url=upload.url, path=upload.path, token=upload.token, expires_at=upload.expires_at
        ),
    )


@router.post(
    "/documents/{document_id}/process",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Document,
    responses=error_responses(401, 404, 409, 422, 429, 502, 503),
)
async def process_document(
    document_id: UUID,
    user_id: CurrentUserId,
    session: SessionDep,
    storage: StorageDep,
    queue: QueueDep,
) -> Document:
    """Check the uploaded PDF (exists, real PDF, page limit) and queue generation."""
    settings = get_settings()
    doc = await owned_document(session, user_id, document_id, for_update=True)
    if doc.status == "ready":
        raise InvalidState("This deck is already ready.", context={"status": doc.status})
    if doc.status == "failed":
        raise InvalidState(
            "This deck couldn't be generated. Use Retry to try again.",
            context={"status": doc.status},
        )
    if doc.source_type != "pdf" or doc.status != "queued" or doc.page_count is not None:
        raise AlreadyProcessing(context={"document_id": document_id, "status": doc.status})

    path = doc.file_path or pdf_path(user_id, document_id)
    stored = await storage.stat(path)
    if stored is None:
        raise UploadMissing(context={"document_id": document_id})
    too_large = FileTooLarge(
        f"This PDF is larger than {settings.max_upload_mb} MB. Please choose a smaller file.",
        context={"document_id": document_id},
    )
    if stored.size is not None and stored.size > settings.max_upload_bytes:
        raise too_large
    data = await storage.download(path)
    if len(data) > settings.max_upload_bytes:
        raise too_large
    pages = count_pages(data) if looks_like_pdf(data) else None
    if not pages:
        raise InvalidFile(
            "This file isn't a valid PDF. Please upload a PDF file.",
            context={"document_id": document_id, "bytes": len(data)},
        )
    if pages > settings.max_pdf_pages:
        doc.status = "failed"
        doc.error_code = PageLimitExceeded.code
        await _commit(session, document_id=document_id)
        raise PageLimitExceeded(
            f"This PDF has {pages} pages; the limit is {settings.max_pdf_pages}. "
            "Split it into smaller parts and upload them separately.",
            context={"document_id": document_id, "pages": pages},
        )

    doc.page_count = pages
    await _commit(session, document_id=document_id)
    await _enqueue_committed(session, queue, doc)
    await session.refresh(doc)
    return (await documents_out(session, user_id, [doc]))[0]


@router.post(
    "/documents/text",
    status_code=status.HTTP_201_CREATED,
    response_model=Document,
    responses=error_responses(401, 409, 422, 429, 503),
)
async def create_text_document(
    body: CreateTextDocumentRequest, profile: CurrentProfile, session: SessionDep, queue: QueueDep
) -> Document:
    """Create a deck from pasted notes (200-100,000 characters after trimming) and queue
    generation."""
    await take_upload_slot(session, profile.id)
    doc = models.Document(
        id=uuid4(),
        user_id=profile.id,
        title=body.title,
        source_type="text",
        raw_text=body.text,
        generate_kinds=list(body.generate_kinds),
    )
    session.add(doc)
    await _commit(session, document_id=doc.id, text_length=len(body.text))
    await _enqueue_committed(session, queue, doc)
    await session.refresh(doc)
    return _document_out(doc)


@router.get("/documents", response_model=DocumentList, responses=error_responses(401, 429, 503))
async def list_documents(user_id: CurrentUserId, session: SessionDep) -> DocumentList:
    """The user's decks, newest first, with status, card counts, due count and mastery."""
    stmt = (
        select(models.Document)
        .where(models.Document.user_id == user_id)
        .order_by(models.Document.created_at.desc(), models.Document.id.desc())
    )
    with guard("db.list_documents", user_id=user_id):
        docs = list((await session.execute(stmt)).scalars())
    return DocumentList(items=await documents_out(session, user_id, docs))


@router.get(
    "/documents/{document_id}",
    response_model=Document,
    responses=error_responses(401, 404, 422, 429, 503),
)
async def get_document(document_id: UUID, user_id: CurrentUserId, session: SessionDep) -> Document:
    """Deck detail: status, progress (poll every 3 s while generating), counts."""
    doc = await owned_document(session, user_id, document_id)
    return (await documents_out(session, user_id, [doc]))[0]


@router.patch(
    "/documents/{document_id}",
    response_model=Document,
    responses=error_responses(401, 404, 422, 429, 503),
)
async def rename_document(
    document_id: UUID, body: RenameDocumentRequest, user_id: CurrentUserId, session: SessionDep
) -> Document:
    """Rename a deck."""
    doc = await owned_document(session, user_id, document_id, for_update=True)
    doc.title = body.title
    await _commit(session, document_id=document_id)
    await session.refresh(doc)
    return (await documents_out(session, user_id, [doc]))[0]


@router.post(
    "/documents/{document_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Document,
    responses=error_responses(401, 404, 409, 422, 429, 503),
)
async def retry_document(
    document_id: UUID, user_id: CurrentUserId, session: SessionDep, queue: QueueDep
) -> Document:
    """Re-queue a failed deck. The job skips chunks that already finished."""
    doc = await owned_document(session, user_id, document_id, for_update=True)
    if doc.status == "ready":
        raise InvalidState("This deck is already ready.", context={"status": doc.status})
    if doc.status != "failed":
        raise AlreadyProcessing(context={"document_id": document_id, "status": doc.status})
    if doc.error_code in NOT_RETRYABLE:
        raise InvalidState(
            NOT_RETRYABLE[doc.error_code],
            context={"document_id": document_id, "error_code": doc.error_code},
        )
    doc.status = "queued"
    doc.error_code = None
    await _commit(session, document_id=document_id)
    await _enqueue_committed(session, queue, doc)
    await session.refresh(doc)
    return (await documents_out(session, user_id, [doc]))[0]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=error_responses(401, 404, 422, 429, 502, 503),
)
async def delete_document(
    document_id: UUID, user_id: CurrentUserId, session: SessionDep, storage: StorageDep
) -> Response:
    """Delete a deck: its PDF in Storage first, then the row (chunks, cards, states and
    attempts cascade). If Storage fails nothing is deleted."""
    doc = await owned_document(session, user_id, document_id, for_update=True)
    if doc.file_path:
        await storage.delete([doc.file_path])
    stmt = delete(models.Document).where(
        models.Document.id == document_id, models.Document.user_id == user_id
    )
    with guard("db.delete_document", document_id=document_id):
        await session.execute(stmt)
    await _commit(session, document_id=document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/documents/{document_id}/chunks/{chunk_id}",
    response_model=Chunk,
    responses=error_responses(401, 404, 422, 429, 503),
)
async def get_chunk(
    document_id: UUID, chunk_id: UUID, user_id: CurrentUserId, session: SessionDep
) -> Chunk:
    """Source text and page range of a chunk ("show source")."""
    stmt = (
        select(models.Chunk)
        .join(models.Document, models.Document.id == models.Chunk.document_id)
        .where(
            models.Chunk.id == chunk_id,
            models.Chunk.document_id == document_id,
            models.Document.user_id == user_id,
        )
    )
    with guard("db.get_chunk", document_id=document_id, chunk_id=chunk_id):
        chunk = (await session.execute(stmt)).scalar_one_or_none()
    if chunk is None:
        raise NotFound(context={"document_id": document_id, "chunk_id": chunk_id})
    return Chunk.model_validate(chunk)
