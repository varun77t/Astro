"""Chart JSON: output of the calculation layer and input to everything downstream."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChartMeta(BaseModel):
    ayanamsa: str
    ayanamsa_value: float
    house_system: str
    node_type: str
    ephemeris: str
    engine_version: str
    utc: datetime
    local_time: datetime
    tz_name: str
    utc_offset: str  # e.g. "+05:30", shown on the confirmation screen
    offset_overridden: bool
    jd_ut: float


class ChartReliability(BaseModel):
    time_accuracy: Literal["exact", "approximate", "unknown"]
    window_minutes: int  # the birth time was checked +- this many minutes
    ascendant_signs: list[str]  # every ascendant sign possible within the window
    moon_signs: list[str]
    moon_nakshatras: list[str]
    ascendant_reliable: bool
    moon_sign_reliable: bool
    moon_nakshatra_reliable: bool
    navamsa_ascendant_signs: list[str]  # D9 ascendant signs possible within the window
    navamsa_moon_signs: list[str]
    navamsa_ascendant_reliable: bool
    navamsa_moon_reliable: bool
    basis: Literal["ascendant", "moon"]  # what readings should count houses from
    warnings: list[str]


class AscendantPosition(BaseModel):
    longitude: float
    sign: str
    sign_lord: str
    degree_in_sign: float
    nakshatra: str
    nakshatra_lord: str
    pada: int


class PlanetPosition(BaseModel):
    name: str
    longitude: float
    latitude: float
    speed: float
    sign: str
    sign_lord: str
    degree_in_sign: float
    house: int
    house_from_moon: int  # Chandra lagna house, used when the birth time is uncertain
    nakshatra: str
    nakshatra_lord: str
    pada: int
    retrograde: bool
    combust: bool
    dignity: str | None


class House(BaseModel):
    house: int
    sign: str
    lord: str
    lord_house: int  # where this house's lord sits
    occupants: list[str]


class DivisionalPlacement(BaseModel):
    name: str
    sign: str
    house: int


class DivisionalChart(BaseModel):
    ascendant_sign: str
    planets: list[DivisionalPlacement]


class Chart(BaseModel):
    meta: ChartMeta
    reliability: ChartReliability
    ascendant: AscendantPosition
    planets: list[PlanetPosition]
    houses: list[House]
    divisional: dict[str, DivisionalChart]

    def planet(self, name: str) -> PlanetPosition:
        return next(p for p in self.planets if p.name == name)
