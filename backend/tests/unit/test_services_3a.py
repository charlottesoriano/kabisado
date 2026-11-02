"""Small services used by the 3a endpoints: rate limiter, PDF checks, today bounds, cursor,
card payload validation."""

from datetime import UTC, datetime
from uuid import uuid4

import pymupdf
import pytest
from pydantic import ValidationError

from app.ai.schemas import FlashcardPayload, McqPayload
from app.errors import ValidationFailed
from app.routers.cards import decode_cursor, encode_cursor
from app.services.extraction import count_pages, looks_like_pdf
from app.services.ratelimit import FixedWindowLimiter
from app.services.stats import mastery_pct, today_bounds


def make_pdf(pages: int, *, encrypted: bool = False) -> bytes:
    doc = pymupdf.open()  # type: ignore[no-untyped-call]
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1} about photosynthesis.")
    if encrypted:
        encrypted_bytes = doc.tobytes(  # type: ignore[no-untyped-call]
            encryption=pymupdf.PDF_ENCRYPT_AES_256,  # type: ignore[attr-defined]
            owner_pw="o",
            user_pw="u",
        )
        return bytes(encrypted_bytes)
    return bytes(doc.tobytes())  # type: ignore[no-untyped-call]


@pytest.mark.unit
def test_rate_limiter_fixed_window() -> None:
    now = [1000.0]
    limiter = FixedWindowLimiter(clock=lambda: now[0])
    assert all(limiter.hit("u", "b", 3, 60) is None for _ in range(3))
    retry = limiter.hit("u", "b", 3, 60)
    assert retry is not None and 0 < retry <= 60
    assert limiter.hit("other", "b", 3, 60) is None  # per user
    now[0] += 60
    assert limiter.hit("u", "b", 3, 60) is None  # next window


@pytest.mark.unit
def test_pdf_checks() -> None:
    pdf = make_pdf(3)
    assert looks_like_pdf(pdf)
    assert count_pages(pdf) == 3
    assert count_pages(make_pdf(2, encrypted=True)) == 2  # the job reports encrypted_pdf
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    assert not looks_like_pdf(png)
    assert count_pages(b"%PDF-1.7 garbage") is None


@pytest.mark.unit
def test_today_bounds_in_manila() -> None:
    # 2026-10-23 20:00 Manila = 12:00 UTC
    start, end = today_bounds("Asia/Manila", datetime(2026, 10, 23, 12, 0, tzinfo=UTC))
    assert start == datetime(2026, 10, 22, 16, 0, tzinfo=UTC)
    assert end == datetime(2026, 10, 23, 16, 0, tzinfo=UTC)
    # Unknown zone falls back to the default instead of failing
    assert today_bounds("Not/AZone", datetime(2026, 10, 23, 12, 0, tzinfo=UTC))[0] == start


@pytest.mark.unit
def test_mastery_pct() -> None:
    assert mastery_pct(4, 10) == 40
    assert mastery_pct(0, 0) == 0
    assert mastery_pct(1, 3) == 33
    assert mastery_pct(1, 8) == 13  # 12.5 rounds half up


@pytest.mark.unit
def test_cursor_round_trip_and_garbage() -> None:
    created, card_id = datetime(2026, 10, 1, 8, 30, tzinfo=UTC), uuid4()
    assert decode_cursor(encode_cursor(created, card_id)) == (created, card_id)
    with pytest.raises(ValidationFailed):
        decode_cursor("not-a-cursor!!")


@pytest.mark.unit
def test_card_payload_rules() -> None:
    FlashcardPayload(front="What is ATP?", back="Energy currency")
    with pytest.raises(ValidationError):
        FlashcardPayload(front="Hi", back="x")  # front < 5 chars
    good = {
        "question": "Which organelle makes ATP?",
        "options": ["Mitochondrion", "Ribosome", "Nucleus", "Golgi"],
        "answer_index": 0,
        "explanation": "Mitochondria run cellular respiration.",
    }
    McqPayload(**good)
    for bad in (
        {**good, "options": ["A", "a ", "B", "C"]},  # duplicate (case/space)
        {**good, "options": ["A", "B", "C"]},  # 3 options
        {**good, "answer_index": 5},
    ):
        with pytest.raises(ValidationError):
            McqPayload(**bad)
