import pytest

from app.config import Settings
from app.jobs.app import _libpq_url


@pytest.mark.unit
def test_csv_fields_split_and_trim() -> None:
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        clerk_authorized_parties="https://a.example, http://localhost:3000 ,",
        llm_bulk_models="groq/x,cerebras/y",
    )
    assert s.authorized_parties == ["https://a.example", "http://localhost:3000"]
    assert s.bulk_models == ["groq/x", "cerebras/y"]
    assert s.verify_models == []


@pytest.mark.unit
def test_defaults_without_env() -> None:
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.max_pdf_pages == 50
    assert s.max_upload_mb == 20
    assert s.code_runner == "judge0"
    assert s.embedding_model == "BAAI/bge-small-en-v1.5"


@pytest.mark.unit
def test_worker_url_strips_sqlalchemy_driver() -> None:
    assert _libpq_url("postgresql+asyncpg://u:p@h:5432/db") == "postgresql://u:p@h:5432/db"
    assert _libpq_url("postgresql://u@h/db") == "postgresql://u@h/db"
