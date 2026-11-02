"""The real Procrastinate queue against the test database (schema ``procrastinate``)."""

from collections.abc import AsyncIterator
from uuid import uuid4

import psycopg
import pytest
from procrastinate import PsycopgConnector

from app.errors import AlreadyProcessing
from app.jobs.app import _libpq_url, _use_procrastinate_schema
from app.jobs.app import app as procrastinate_app
from app.jobs.queue import ProcrastinateQueue
from tests.conftest import TEST_DATABASE_URL, needs_db

pytestmark = [pytest.mark.integration, needs_db]


@pytest.fixture
async def real_queue(migrated_db: str) -> AsyncIterator[ProcrastinateQueue]:
    connector = PsycopgConnector(
        conninfo=_libpq_url(TEST_DATABASE_URL), configure=_use_procrastinate_schema
    )
    with procrastinate_app.replace_connector(connector) as app_with_test_db:
        queue = ProcrastinateQueue(app_with_test_db)
        yield queue
        await queue.aclose()


async def test_enqueue_once_per_document(real_queue: ProcrastinateQueue) -> None:
    document_id = uuid4()
    await real_queue.enqueue_generation(document_id)
    with pytest.raises(AlreadyProcessing):
        await real_queue.enqueue_generation(document_id)

    async with await psycopg.AsyncConnection.connect(
        _libpq_url(TEST_DATABASE_URL), autocommit=True
    ) as conn:
        rows = await (
            await conn.execute(
                "select task_name, status, args->>'document_id' from "
                "procrastinate.procrastinate_jobs where queueing_lock = %s",
                (str(document_id),),
            )
        ).fetchall()
        assert rows == [("generate_document", "todo", str(document_id))]
        await conn.execute(
            "delete from procrastinate.procrastinate_jobs where queueing_lock = %s",
            (str(document_id),),
        )
