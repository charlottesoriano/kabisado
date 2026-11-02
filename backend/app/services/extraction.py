"""PyMuPDF text extraction per page; scanned-PDF (< 50 chars/page avg) and encrypted-PDF
detection.

The upload checks used by ``POST /documents/{id}/process`` live here too: magic bytes and
page count. Text extraction for the job comes in build step 4.
"""

import pymupdf

PDF_MAGIC = b"%PDF-"


def looks_like_pdf(data: bytes) -> bool:
    """True if the file starts with the PDF magic bytes (leading whitespace tolerated)."""
    return data.lstrip()[: len(PDF_MAGIC)] == PDF_MAGIC


def count_pages(data: bytes) -> int | None:
    """Page count of a PDF, or ``None`` if PyMuPDF can't open it. Works for encrypted PDFs
    (the job reports those as ``encrypted_pdf``)."""
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:  # type: ignore[no-untyped-call]
            return int(doc.page_count)
    except Exception:
        return None
