from typing import Literal

from pydantic import BaseModel


class Place(BaseModel):
    name: str
    display_name: str  # "Mysuru, Karnataka, India"
    lat: float
    lon: float
    country_code: str | None
    tz_name: str
    source: Literal["photon", "nominatim"]


class GeocodeResponse(BaseModel):
    results: list[Place]


class TimezoneResponse(BaseModel):
    tz_name: str
