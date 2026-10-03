import datetime as dt

from pydantic import BaseModel, Field

from app.schemas.birth import BirthInput


class DashaRequest(BirthInput):
    as_of: dt.datetime | None = Field(
        default=None,
        description="Which moment counts as 'now' for the current period; default: now",
    )


class DashaPeriod(BaseModel):
    lord: str
    start: dt.datetime
    end: dt.datetime


class Mahadasha(DashaPeriod):
    antardashas: list[DashaPeriod]


class CurrentDasha(BaseModel):
    mahadasha: DashaPeriod
    antardasha: DashaPeriod
    pratyantardasha: DashaPeriod


class DashaResponse(BaseModel):
    system: str = "vimshottari"
    year_days: float
    moon_nakshatra: str
    first_lord: str
    balance_years: float  # left of the first mahadasha at birth
    as_of: dt.datetime
    mahadashas: list[Mahadasha]  # one 120-year cycle from the period running at birth
    current: CurrentDasha | None  # None before birth or after the cycle
    pratyantardashas: list[DashaPeriod]  # inside the current antardasha
    # The Moon moves ~0.5° an hour, so a loose birth time slides every date.
    timing_reliable: bool  # False when the Moon's nakshatra changes within the birth-time window
    uncertainty_days: float | None  # how far boundaries could move within the window
