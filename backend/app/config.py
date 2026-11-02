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

    # Postgres (Supabase session pooler)
    database_url: str = ""
    worker_database_url: str = ""

    # Supabase Storage (backend only)
    supabase_url: str = ""
    supabase_service_role_key: SecretStr = SecretStr("")

    # Clerk
    clerk_secret_key: SecretStr = SecretStr("")
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""
    clerk_authorized_parties: str = ""
    clerk_webhook_secret: SecretStr = SecretStr("")

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

    # Observability
    sentry_dsn: str = ""

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
