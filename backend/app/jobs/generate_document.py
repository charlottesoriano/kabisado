"""The ``generate_document(document_id)`` background pipeline (MDs/03-backend.md section 4).

Stages: extract, clean, chunk, classify, embed, generate, deduplicate, create states, finish.
Resumable: chunks with ``gen_status = done`` are skipped. Implemented in build step 5.

BACKSTOP REQUIRED (step 5): the job must re-check the file itself and not trust the API's
``/process`` checks. ``POST /documents/{id}/retry`` and a re-upload to the same path (signed
upload URLs allow overwrite) can put a different file behind a deck than the one ``/process``
inspected. Before extracting, the job must:

- re-count the pages and, above ``MAX_PDF_PAGES``, fail the deck with
  ``error_code = page_limit_exceeded``;
- fail with ``invalid_file`` if PyMuPDF can't open the file, and ``encrypted_pdf`` if it needs
  a password.

Retry refuses ``page_limit_exceeded`` and ``invalid_file`` (the student must upload a new
file), so these codes must only be used for problems with the file itself.

The job must also never delete the uploaded PDF: it is kept so the app can later open it at a
chunk's page.
"""

from app.jobs.app import app


@app.task(name="generate_document")
async def generate_document(document_id: str) -> None:
    """Placeholder task; the pipeline is not implemented yet."""
