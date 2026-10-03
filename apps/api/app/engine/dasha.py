"""Vimshottari dasha: the 120-year cycle of planetary periods.

At birth the Moon sits in a nakshatra ruled by one of nine lords. That lord's mahadasha is
running, and the share of the nakshatra the Moon has still to cross is the share of the
mahadasha left (the "balance"). The other lords follow in a fixed order. Each mahadasha splits
into nine antardashas in the same order, starting with its own lord, sized in proportion to
the lords' years; each antardasha splits into pratyantardashas the same way.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.engine.constants import NAKSHATRA_LORD_CYCLE
from app.engine.nakshatra import nakshatra_of

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}
TOTAL_YEARS = 120

# A dasha year as a Julian year of 365.25 days, the most common convention (also AstroSage's).
YEAR_DAYS = 365.25


@dataclass(frozen=True)
class Period:
    lord: str
    start: datetime
    end: datetime
    children: list["Period"] = field(default_factory=list)

    def contains(self, moment: datetime) -> bool:
        return self.start <= moment < self.end


def lords_from(lord: str) -> list[str]:
    """The nine lords in Vimshottari order, starting with `lord`."""
    i = NAKSHATRA_LORD_CYCLE.index(lord)
    return NAKSHATRA_LORD_CYCLE[i:] + NAKSHATRA_LORD_CYCLE[:i]


def _years(n: float) -> timedelta:
    return timedelta(days=n * YEAR_DAYS)


def subdivide(lord: str, start: datetime, end: datetime) -> list[Period]:
    """Split a period into nine sub-periods, starting with its own lord."""
    span = end - start
    out, t = [], start
    for sub in lords_from(lord):
        nxt = t + span * DASHA_YEARS[sub] / TOTAL_YEARS
        out.append(Period(sub, t, nxt))
        t = nxt
    # Absorb float drift so consecutive periods tile exactly.
    out[-1] = Period(out[-1].lord, out[-1].start, end)
    return out


@dataclass(frozen=True)
class DashaSequence:
    moon_longitude: float
    nakshatra: str
    first_lord: str
    balance_years: float  # left of the first mahadasha at birth
    epoch: datetime  # when the first mahadasha would have begun; birth falls inside it
    mahadashas: list[Period]


def vimshottari(moon_longitude: float, birth_utc: datetime, cycles: int = 1) -> DashaSequence:
    """Mahadashas from the one running at birth through a full 120-year cycle, with antardashas."""
    nak = nakshatra_of(moon_longitude)
    lord = nak.lord
    elapsed = nak.fraction_traversed * DASHA_YEARS[lord]
    epoch = birth_utc - _years(elapsed)

    mahadashas, t = [], epoch
    for _ in range(cycles):
        for md_lord in lords_from(lord):
            end = t + _years(DASHA_YEARS[md_lord])
            mahadashas.append(Period(md_lord, t, end, subdivide(md_lord, t, end)))
            t = end

    return DashaSequence(
        moon_longitude=moon_longitude,
        nakshatra=nak.name,
        first_lord=lord,
        balance_years=DASHA_YEARS[lord] - elapsed,
        epoch=epoch,
        mahadashas=mahadashas,
    )


def running_at(periods: list[Period], moment: datetime) -> Period | None:
    return next((p for p in periods if p.contains(moment)), None)
