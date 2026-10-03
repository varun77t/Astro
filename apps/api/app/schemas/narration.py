from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.reading import Area, Reading, ReadingRequest

Language = Literal["en"]  # Hindi and Kannada later; the validator's checks are English-only


class NarrationRequest(ReadingRequest):
    language: Language = "en"


class NarratedPoint(BaseModel):
    text: str = Field(min_length=1)
    rule_ids: list[str] = Field(min_length=1)  # the rules this sentence rests on


class LLMReading(BaseModel):
    """What the model must return (validated before anyone sees it)."""

    summary: str = Field(min_length=1)
    strengths: list[NarratedPoint] = []
    watch_points: list[NarratedPoint] = []
    current_period_note: NarratedPoint | None = None


class Narration(BaseModel):
    area: Area
    language: Language
    # "llm": written by a model from the matched rules. "rules": the rule texts as they are,
    # because no provider was available or none produced a valid answer in time.
    mode: Literal["llm", "rules"]
    provider: str | None
    model: str | None
    cached: bool
    summary: str
    strengths: list[NarratedPoint]
    watch_points: list[NarratedPoint]
    current_period: list[NarratedPoint]
    reading: Reading  # the rule reading underneath, for "Why this?"
    rules_version: str
    limit_reached: bool = False  # rule texts because today's AI allowance is used up
