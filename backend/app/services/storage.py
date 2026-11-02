"""File storage (Supabase Storage, service role, backend only).

Uploaded PDFs live in the private bucket ``STORAGE_BUCKET`` (``uploads``) at
``{user_id}/{document_id}.pdf``. They are kept after processing (deleted only with the deck or
the user), so a later feature can open the PDF at a chunk's page.

Routes depend on the ``Storage`` protocol (``get_storage``); tests swap in a recording fake.

Signed upload URLs: Supabase fixes their lifetime at 2 hours (no option to shorten it), so
``expires_at`` is read from the URL's token rather than assumed. Spec deviation from the
10-minute expiry in MDs/03-backend.md section 9.

Create the bucket once per environment::

    uv run python -m app.services.storage --ensure-bucket
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import httpx
import jwt
from storage3 import AsyncStorageClient
from storage3.exceptions import StorageApiError
from storage3.types import CreateSignedUploadUrlOptions

from app.config import get_settings
from app.errors import ServiceUnavailable, guard

SUPABASE_UPLOAD_URL_LIFETIME = timedelta(hours=2)
PDF_MIME = "application/pdf"


def pdf_path(user_id: str, document_id: object) -> str:
    return f"{user_id}/{document_id}.pdf"


@dataclass(frozen=True)
class SignedUpload:
    url: str
    path: str
    token: str
    expires_at: datetime


@dataclass(frozen=True)
class StoredObject:
    path: str
    size: int | None
    content_type: str | None


class Storage(Protocol):
    async def create_signed_upload_url(self, path: str) -> SignedUpload: ...

    async def create_signed_download_url(self, path: str, expires_in: int) -> str: ...

    async def stat(self, path: str) -> StoredObject | None: ...

    async def download(self, path: str) -> bytes: ...

    async def delete(self, paths: list[str]) -> None: ...

    async def delete_prefix(self, prefix: str) -> int: ...

    async def aclose(self) -> None: ...


def _token_expiry(token: str) -> datetime:
    try:
        exp = jwt.decode(token, options={"verify_signature": False}).get("exp")
    except jwt.PyJWTError:
        exp = None
    if isinstance(exp, int | float):
        return datetime.fromtimestamp(exp, tz=UTC)
    return datetime.now(UTC) + SUPABASE_UPLOAD_URL_LIFETIME


def _is_missing(exc: StorageApiError) -> bool:
    return str(exc.status) in ("400", "404") and "not found" in str(exc.message).lower()


class SupabaseStorage:
    def __init__(self, url: str, service_key: str, bucket: str, timeout: float) -> None:
        headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
        self._http = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        self._client = AsyncStorageClient(
            f"{url.rstrip('/')}/storage/v1/", headers, http_client=self._http
        )
        self.bucket = bucket

    @property
    def _files(self) -> Any:
        return self._client.from_(self.bucket)

    async def create_signed_upload_url(self, path: str) -> SignedUpload:
        with guard("storage.create_signed_upload_url", path=path):
            # upsert: the student can re-upload to the same document after a failed upload.
            data = await self._files.create_signed_upload_url(
                path, CreateSignedUploadUrlOptions(upsert="true")
            )
        return SignedUpload(
            url=data["signed_url"],
            path=path,
            token=data["token"],
            expires_at=_token_expiry(data["token"]),
        )

    async def create_signed_download_url(self, path: str, expires_in: int) -> str:
        with guard("storage.create_signed_download_url", path=path):
            url: str = await self._files.create_signed_url(path, expires_in)
        return url

    async def stat(self, path: str) -> StoredObject | None:
        try:
            with guard("storage.stat", path=path):
                info = await self._files.info(path)
        except Exception as exc:
            cause = exc.__cause__
            if isinstance(cause, StorageApiError) and _is_missing(cause):
                return None
            raise
        metadata = info.get("metadata") or {}
        size = info.get("size", metadata.get("size"))
        content_type = info.get("content_type", metadata.get("mimetype"))
        return StoredObject(
            path=path,
            size=int(size) if size is not None else None,
            content_type=content_type,
        )

    async def download(self, path: str) -> bytes:
        with guard("storage.download", path=path):
            data: bytes = await self._files.download(path)
        return data

    async def delete(self, paths: list[str]) -> None:
        if paths:
            with guard("storage.delete", paths=len(paths)):
                await self._files.remove(paths)

    async def delete_prefix(self, prefix: str) -> int:
        """Delete every object directly under ``prefix/`` (a user's folder)."""
        deleted = 0
        prefix = prefix.rstrip("/")
        for _ in range(100):  # 100 pages x 1000 objects is far beyond a user's files
            with guard("storage.list", prefix=prefix):
                entries = await self._files.list(prefix, {"limit": 1000, "offset": 0})
            names = [e["name"] for e in entries if e.get("id")]  # folders have no id
            if not names:
                break
            await self.delete([f"{prefix}/{name}" for name in names])
            deleted += len(names)
        return deleted

    async def ensure_bucket(self, file_size_limit: int) -> str:
        options: Any = {
            "public": False,
            "file_size_limit": file_size_limit,
            "allowed_mime_types": [PDF_MIME],
        }
        try:
            with guard("storage.get_bucket", bucket=self.bucket):
                await self._client.get_bucket(self.bucket)
        except Exception as exc:
            cause = exc.__cause__
            if not (isinstance(cause, StorageApiError) and _is_missing(cause)):
                raise
            with guard("storage.create_bucket", bucket=self.bucket):
                await self._client.create_bucket(self.bucket, options=options)
            return "created"
        with guard("storage.update_bucket", bucket=self.bucket):
            await self._client.update_bucket(self.bucket, options)
        return "updated"

    async def aclose(self) -> None:
        await self._http.aclose()


_storage: SupabaseStorage | None = None


def _build() -> SupabaseStorage:
    settings = get_settings()
    key = settings.supabase_service_role_key.get_secret_value()
    if not (settings.supabase_url and key):
        raise ServiceUnavailable(
            operation="storage.configure", context={"reason": "supabase_not_configured"}
        )
    return SupabaseStorage(
        settings.supabase_url, key, settings.storage_bucket, settings.storage_timeout_seconds
    )


def get_storage() -> Storage:
    """FastAPI dependency: the process-wide storage client (built on first use)."""
    global _storage
    if _storage is None:
        _storage = _build()
    return _storage


async def close_storage() -> None:
    global _storage
    if _storage is not None:
        await _storage.aclose()
    _storage = None


async def _ensure_bucket() -> str:
    storage = _build()
    try:
        return await storage.ensure_bucket(get_settings().max_upload_bytes)
    finally:
        await storage.aclose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.services.storage")
    parser.add_argument(
        "--ensure-bucket",
        action="store_true",
        help="Create (or update) the private uploads bucket: PDF only, MAX_UPLOAD_MB limit.",
    )
    args = parser.parse_args(argv)
    if not args.ensure_bucket:
        parser.print_help()
        return 2
    settings = get_settings()
    result = asyncio.run(_ensure_bucket())
    print(
        f"Bucket '{settings.storage_bucket}' {result}: private, application/pdf, "
        f"{settings.max_upload_mb} MiB limit."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
