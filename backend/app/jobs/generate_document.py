"""The ``generate_document(document_id)`` background pipeline (MDs/03-backend.md section 4).

Stages: extract, clean, chunk, classify, embed, generate, deduplicate, create states, finish.
Resumable: chunks with ``gen_status = done`` are skipped. Implemented in build step 5.
"""

from app.jobs.app import app


@app.task(name="generate_document")
async def generate_document(document_id: str) -> None:
    """Placeholder task; the pipeline is not implemented yet."""
