import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TimeAccuracy = Literal["exact", "approximate", "unknown"]

# Birth times are often rounded, so even an "exact" time is checked +-5 minutes.
EXACT_WINDOW_MINUTES = 5
DEFAULT_APPROXIMATE_WINDOW_MINUTES = 30
UNKNOWN_TIME_ASSUMED = dt.time(12, 0)
UNKNOWN_WINDOW_MINUTES = 12 * 60


class BirthInput(BaseModel):
    """Birth details after the place has been resolved to coordinates and a timezone."""

    date: dt.date
    time: dt.time | None = Field(default=None, description="Local wall-clock time; omit if unknown")
    time_accuracy: TimeAccuracy = "exact"
    time_window_minutes: int | None = Field(
        default=None,
        ge=1,
        le=360,
        description="For approximate times: the time is correct to within +- this many minutes.",
    )
    tz_name: str = Field(examples=["Asia/Kolkata"], description="IANA timezone of the birth place")
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180, description="East positive")
    fold: Literal[0, 1] | None = Field(
        default=None,
        description="Only needed when the local time occurred twice (DST fall-back): "
        "0 = first occurrence, 1 = second.",
    )
    utc_offset_minutes: int | None = Field(
        default=None,
        ge=-12 * 60,
        le=14 * 60,
        description="Overrides the timezone's historical offset, e.g. 291 for Bombay Time.",
    )

    @model_validator(mode="after")
    def _check(self) -> "BirthInput":
        if not 1800 <= self.date.year <= 2100:
            raise ValueError("Birth year must be between 1800 and 2100.")
        if self.time is None and self.time_accuracy != "unknown":
            raise ValueError("Birth time is required unless time_accuracy is 'unknown'.")
        return self

    def local_datetime(self) -> dt.datetime:
        clock = UNKNOWN_TIME_ASSUMED if self.time_accuracy == "unknown" else self.time
        return dt.datetime.combine(self.date, clock.replace(tzinfo=None))

    def window_minutes(self) -> int:
        if self.time_accuracy == "unknown":
            return UNKNOWN_WINDOW_MINUTES
        if self.time_accuracy == "approximate":
            return self.time_window_minutes or DEFAULT_APPROXIMATE_WINDOW_MINUTES
        return EXACT_WINDOW_MINUTES


class BirthResolution(BaseModel):
    """What the confirmation screen shows before a chart is generated."""

    local_time: dt.datetime
    utc: dt.datetime
    utc_offset: str  # "+05:30"
    tz_name: str
    tz_abbreviation: str | None  # "IST", "EDT"; None when an offset override is used
    is_dst: bool
    offset_overridden: bool
    time_accuracy: TimeAccuracy
    time_assumed: bool  # True when the time was unknown and noon was used
    window_minutes: int
    notes: list[str]
