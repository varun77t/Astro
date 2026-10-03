from functools import lru_cache

from timezonefinder import TimezoneFinder


@lru_cache(maxsize=1)
def _finder() -> TimezoneFinder:
    return TimezoneFinder()  # loads polygon data once (~tens of ms)


def timezone_for(lat: float, lon: float) -> str | None:
    """IANA timezone at a coordinate. Open ocean gets an Etc/GMT±N zone."""
    return _finder().timezone_at(lat=lat, lng=lon)
