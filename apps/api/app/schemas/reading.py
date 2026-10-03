import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.birth import BirthInput

Area = Literal["education", "career", "money", "health", "relationships"]
AREAS: tuple[Area, ...] = ("education", "career", "money", "health", "relationships")
Tone = Literal["supportive", "cautionary", "neutral"]


class ReadingRequest(BirthInput):
    as_of: dt.datetime | None = Field(
        default=None, description="Which moment counts as 'now' for the current period"
    )


class Because(BaseModel):
    text: str  # "Jupiter is in your 5th house"
    planets: list[str]
    houses: list[int]  # counted from the reading's basis


class Statement(BaseModel):
    rule_id: str
    title: str
    text: str
    tone: Tone
    weight: float
    # "sure": holds across the whole birth-time window. "possible": holds at the given time
    # but not everywhere in the window, so it depends on the exact birth time.
    certainty: Literal["sure", "possible"]
    because: list[Because]
    source: str


class Reading(BaseModel):
    area: Area
    title: str
    basis: Literal["ascendant", "moon"]
    summary: str
    strengths: list[Statement]  # supportive and neutral points, strongest first
    watch_points: list[Statement]  # cautionary points
    current_period: list[Statement]  # how the running dasha touches this area
    disclaimer: str | None
    matched_rule_ids: list[str]  # everything that matched, before trimming to the top few


class ReadingsResponse(BaseModel):
    rules_version: str
    as_of: dt.datetime
    note: str
    readings: list[Reading]
