"""Pydantic schemas for AI output (MDs/03-backend.md section 5.3).

The payload models are also what ``PATCH /cards/{id}`` validates student edits against, so a
card is held to the same rules whether the AI or the student wrote it. Problem templates
(section 5.6) are added in build step 5.
"""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

Text300 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=300)]
Text600 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=400)]
Option = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Explanation = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=10, max_length=600)
]


class FlashcardPayload(BaseModel):
    """``cards.payload`` for ``type = flashcard``."""

    front: Text300
    back: Text600


class McqPayload(BaseModel):
    """``cards.payload`` for ``type = mcq``. Options are in the author's order; quizzes shuffle
    them per attempt."""

    question: Question
    options: list[Option] = Field(min_length=4, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    explanation: Explanation

    @field_validator("options")
    @classmethod
    def distinct(cls, v: list[str]) -> list[str]:
        if len({o.strip().lower() for o in v}) != 4:
            raise ValueError("options must be distinct")
        return v


class Flashcard(FlashcardPayload):
    topic: str


class MCQ(McqPayload):
    topic: str


class ChunkCards(BaseModel):
    skip: bool = False  # true for table of contents, references, fluff
    flashcards: list[Flashcard] = Field(max_length=6)
    mcqs: list[MCQ] = Field(max_length=4)
