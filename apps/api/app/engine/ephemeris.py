"""Thin wrapper around Swiss Ephemeris. All longitudes returned are sidereal (Lahiri).

Swiss Ephemeris keeps the sidereal mode as process-global state, so every call that
depends on it takes SWE_LOCK and re-applies the mode first.
"""

import threading
from dataclasses import dataclass

import swisseph as swe

from app.engine.constants import NODE_TYPE, normalize

SWE_LOCK = threading.Lock()

# Moshier = analytic ephemeris built into the library (no .se1 data files). Its error is
# well under 1 arcsecond for planets in historical/modern dates, far inside our tolerance.
BASE_FLAGS = swe.FLG_MOSEPH
SIDEREAL_FLAGS = BASE_FLAGS | swe.FLG_SIDEREAL | swe.FLG_SPEED

_SWE_BODIES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}
_NODE_BODY = {"mean": swe.MEAN_NODE, "true": swe.TRUE_NODE}


@dataclass(frozen=True)
class BodyPosition:
    name: str
    longitude: float  # sidereal, degrees [0, 360)
    latitude: float
    speed: float  # degrees/day in longitude; negative = retrograde

    @property
    def retrograde(self) -> bool:
        return self.speed < 0


def _set_sidereal_mode() -> None:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


def ayanamsa(jd_ut: float) -> float:
    """The Lahiri ayanamsa actually subtracted from tropical positions at this moment."""
    with SWE_LOCK:
        _set_sidereal_mode()
        return swe.get_ayanamsa_ex_ut(jd_ut, BASE_FLAGS)[1]


def body_positions(jd_ut: float, node_type: str = NODE_TYPE) -> list[BodyPosition]:
    """Sidereal positions of the 7 classical planets plus Rahu and Ketu, in PLANETS order."""
    with SWE_LOCK:
        _set_sidereal_mode()
        positions = []
        for name, body in _SWE_BODIES.items():
            xx = swe.calc_ut(jd_ut, body, SIDEREAL_FLAGS)[0]
            positions.append(BodyPosition(name, normalize(xx[0]), xx[1], xx[3]))
        xx = swe.calc_ut(jd_ut, _NODE_BODY[node_type], SIDEREAL_FLAGS)[0]

    rahu = BodyPosition("Rahu", normalize(xx[0]), xx[1], xx[3])
    ketu = BodyPosition("Ketu", normalize(xx[0] + 180.0), -xx[1], xx[3])
    return positions + [rahu, ketu]


def moon_longitude(jd_ut: float) -> float:
    with SWE_LOCK:
        _set_sidereal_mode()
        return normalize(swe.calc_ut(jd_ut, swe.MOON, SIDEREAL_FLAGS)[0][0])


def ascendant_longitude(jd_ut: float, lat: float, lon: float) -> float:
    """Sidereal ascendant (lagna) for a geographic latitude/longitude (east positive)."""
    with SWE_LOCK:
        _set_sidereal_mode()
        _, ascmc = swe.houses_ex(jd_ut, lat, lon, b"W", swe.FLG_SIDEREAL)
    return normalize(ascmc[0])
