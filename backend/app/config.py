"""Application settings (pydantic-settings), read from the environment and ``backend/.env``.

Variable names follow MDs/01-stack.md section 8. Every field has a safe default so the app can
start (and tests can run) without real keys; features that need a key check for it at use time.
Model names, provider order and limits come from here, never from hard-coded values.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Runtime environment. Anything other than "production" counts as local/dev and adds a
    # ``debug`` object to error responses (exception type and message). Default is the safe one.
    app_env: Literal["local", "development", "test", "production"] = "production"

    # Postgres (Supabase session pooler)
    database_url: str = ""
    worker_database_url: str = ""
    db_pool_size: int = 5
    db_max_overflow: int = 5

    # Supabase Storage (backend only)
    supabase_url: str = ""
    supabase_service_role_key: SecretStr = SecretStr("")
    storage_bucket: str = "uploads"
    storage_timeout_seconds: float = 20.0
    signed_url_ttl_seconds: int = 600  # download URLs; Supabase fixes upload URLs at 2 h

    # Clerk
    clerk_secret_key: SecretStr = SecretStr("")
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""
    clerk_authorized_parties: str = ""
    clerk_webhook_secret: SecretStr = SecretStr("")
    clerk_clock_skew_seconds: int = 10
    clerk_jwks_cache_seconds: int = 3600
    clerk_jwks_min_refetch_seconds: int = 10  # throttle refetches triggered by unknown ``kid``
    clerk_jwks_timeout_seconds: float = 5.0

    # LLM providers
    groq_api_key: SecretStr = SecretStr("")
    gemini_api_key: SecretStr = SecretStr("")
    cerebras_api_key: SecretStr = SecretStr("")
    openrouter_api_key: SecretStr = SecretStr("")

    # Model groups, comma-separated in fallback order
    llm_bulk_models: str = ""
    llm_interactive_models: str = ""
    llm_verify_models: str = ""

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Code execution
    code_runner: Literal["judge0", "wasm"] = "judge0"
    judge0_api_url: str = ""
    judge0_api_key: SecretStr = SecretStr("")

    # Limits
    max_pdf_pages: int = 50
    max_upload_mb: int = 20
    uploads_per_day: int = 20  # PDF uploads and pasted notes, per user, per local calendar day

    # Rate limits (per user, in-memory fixed windows)
    rate_limit_default_per_min: int = 120
    rate_limit_ai_per_min: int = 10
    rate_limit_ai_per_day: int = 100

    # Observability
    sentry_dsn: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def authorized_parties(self) -> list[str]:
        return _split_csv(self.clerk_authorized_parties)

    @property
    def bulk_models(self) -> list[str]:
        return _split_csv(self.llm_bulk_models)

    @property
    def interactive_models(self) -> list[str]:
        return _split_csv(self.llm_interactive_models)

    @property
    def verify_models(self) -> list[str]:
        return _split_csv(self.llm_verify_models)


@lru_cache
def get_settings() -> Settings:
    return Settings()
