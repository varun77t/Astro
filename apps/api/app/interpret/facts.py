"""The chart reduced to what rules can ask about.

Built straight from raw longitudes so the same code serves the birth moment, the samples
across a loose birth-time window, and the synthetic charts in the rule tests. House numbers
are counted from the reading's basis: the Lagna, or the Moon's sign when the birth time
can't fix the Lagna.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from app.engine.constants import PLANETS, SIGN_LORDS, SIGNS, sign_index
from app.engine.ephemeris import ascendant_longitude, body_positions
from app.engine.strength import dignity, is_combust
from app.engine.vargas import navamsa_sign_index

Basis = Literal["ascendant", "moon"]
PeriodLevel = Literal["maha", "antar"]

# Graha drishti, counted in whole signs from the planet (1 = its own sign). Every planet
# aspects the 7th; Mars, Jupiter and Saturn have special aspects. Rahu and Ketu cast none
# here: the classics disagree on them, so rules don't lean on node aspects.
ASPECTS = {
    "Sun": (7,),
    "Moon": (7,),
    "Mercury": (7,),
    "Venus": (7,),
    "Mars": (4, 7, 8),
    "Jupiter": (5, 7, 9),
    "Saturn": (3, 7, 10),
    "Rahu": (),
    "Ketu": (),
}

ALWAYS_BENEFIC = ("Jupiter", "Venus", "Mercury")
ALWAYS_MALEFIC = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class PlanetFacts:
    name: str
    longitude: float
    sign: int  # 0 = Aries
    house: int  # counted from the basis
    house_from_moon: int
    dignity: str | None
    retrograde: bool
    combust: bool
    d9_sign: int
    d9_dignity: str | None  # exalted / own / debilitated in the navamsa, else None

    @property
    def vargottama(self) -> bool:
        return self.sign == self.d9_sign


@dataclass(frozen=True)
class PeriodFacts:
    lord: str
    end: datetime


@dataclass(frozen=True)
class ChartFacts:
    basis: Basis
    first_house: int  # sign index of house 1: the Lagna, or the Moon's sign
    lagna: int | None  # the real Lagna sign, None when unknown
    planets: dict[str, PlanetFacts]
    moon_waxing: bool
    periods: dict[str, PeriodFacts] = field(default_factory=dict)

    def house_sign(self, house: int) -> int:
        return (self.first_house + house - 1) % 12

    def lord_of(self, house: int) -> str:
        return SIGN_LORDS[SIGNS[self.house_sign(house)]]

    def houses_ruled_by(self, planet: str) -> list[int]:
        return [h for h in range(1, 13) if self.lord_of(h) == planet]

    def in_house(self, house: int) -> list[str]:
        return [p.name for p in self.planets.values() if p.house == house]

    def aspecting(self, sign: int) -> list[str]:
        """Planets whose drishti falls on this sign."""
        return [
            p.name
            for p in self.planets.values()
            if any((p.sign + n - 1) % 12 == sign for n in ASPECTS[p.name])
        ]

    @property
    def benefics(self) -> set[str]:
        return {*ALWAYS_BENEFIC, *(("Moon",) if self.moon_waxing else ())}

    @property
    def malefics(self) -> set[str]:
        return {*ALWAYS_MALEFIC, *(() if self.moon_waxing else ("Moon",))}


def _house(sign: int, first: int) -> int:
    return (sign - first) % 12 + 1


def _d9_dignity(planet: str, d9_sign: int) -> str | None:
    d = dignity(planet, d9_sign * 30.0 + 29.0)  # past every moolatrikona range
    return d if d in ("exalted", "own", "debilitated") else None


def facts_from_longitudes(
    longitudes: dict[str, float],
    *,
    retrograde: dict[str, bool] | None = None,
    ascendant: float | None,
    basis: Basis,
    periods: dict[str, PeriodFacts] | None = None,
) -> ChartFacts:
    retrograde = retrograde or {}
    sun, moon = longitudes["Sun"], longitudes["Moon"]
    moon_sign = sign_index(moon)
    lagna = sign_index(ascendant) if ascendant is not None else None
    if basis == "ascendant" and lagna is None:
        raise ValueError("an ascendant basis needs the ascendant")
    first = lagna if basis == "ascendant" else moon_sign

    planets = {}
    for name in PLANETS:
        lon = longitudes[name]
        sign = sign_index(lon)
        retro = retrograde.get(name, name in ("Rahu", "Ketu"))
        d9 = navamsa_sign_index(lon)
        planets[name] = PlanetFacts(
            name=name,
            longitude=lon,
            sign=sign,
            house=_house(sign, first),
            house_from_moon=_house(sign, moon_sign),
            dignity=dignity(name, lon),
            retrograde=retro,
            combust=is_combust(name, lon, sun, retro),
            d9_sign=d9,
            d9_dignity=_d9_dignity(name, d9),
        )
    return ChartFacts(
        basis=basis,
        first_house=first,
        lagna=lagna,
        planets=planets,
        moon_waxing=(moon - sun) % 360 < 180,
        periods=periods or {},
    )


def facts_at(
    jd_ut: float,
    lat: float,
    lon: float,
    basis: Basis,
    periods: dict[str, PeriodFacts] | None = None,
) -> ChartFacts:
    bodies = body_positions(jd_ut)
    return facts_from_longitudes(
        {b.name: b.longitude for b in bodies},
        retrograde={b.name: b.retrograde for b in bodies},
        ascendant=ascendant_longitude(jd_ut, lat, lon),
        basis=basis,
        periods=periods,
    )
