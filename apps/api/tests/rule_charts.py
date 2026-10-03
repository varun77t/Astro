"""Synthetic charts for rule tests, built from the `test:` block each rule carries.

    test: {lagna: Aries, Jupiter: Leo, Mercury: "Virgo 28 R", period: {maha: Sun}}

Planets not named sit in a fixed base layout; a bare sign puts the planet at 15°. Naming
Rahu places Ketu opposite and vice versa. `basis: moon` drops the Lagna and counts houses
from the Moon.
"""

from datetime import UTC, datetime

from app.engine.constants import SIGNS
from app.interpret.facts import ChartFacts, PeriodFacts, facts_from_longitudes

# Lagna Aries: Sun 9th, Moon 11th (waxing), Mars 3rd, Mercury 10th, Jupiter 6th,
# Venus 11th, Saturn 2nd, Rahu 7th, Ketu 1st.
BASE = {
    "Sun": "Sagittarius 10",
    "Moon": "Aquarius 20",
    "Mars": "Gemini 15",
    "Mercury": "Capricorn 20",
    "Jupiter": "Virgo 15",
    "Venus": "Aquarius 5",
    "Saturn": "Taurus 15",
    "Rahu": "Libra 15",
}
PERIOD_END = datetime(2030, 1, 1, tzinfo=UTC)


def _position(text: str) -> tuple[float, bool]:
    parts = str(text).split()
    sign = SIGNS.index(parts[0])
    degree = float(parts[1]) if len(parts) > 1 and parts[1] != "R" else 15.0
    return sign * 30 + degree, parts[-1] == "R"


def chart_from_spec(spec: dict) -> ChartFacts:
    spec = dict(spec)
    lagna = spec.pop("lagna", None)
    basis = spec.pop("basis", "ascendant" if lagna else "moon")
    periods = spec.pop("period", {})

    placed = {**BASE, **spec}
    if "Ketu" in spec and "Rahu" not in spec:
        placed.pop("Rahu")
    lons, retro = {}, {}
    for name, text in placed.items():
        lons[name], retro[name] = _position(text)
    if "Rahu" in lons:
        lons["Ketu"] = (lons["Rahu"] + 180) % 360
    else:
        lons["Rahu"] = (lons["Ketu"] + 180) % 360
    retro["Rahu"] = retro["Ketu"] = True

    maha = periods.get("maha")
    period_facts = {}
    if maha:
        period_facts["maha"] = PeriodFacts(maha, PERIOD_END)
        period_facts["antar"] = PeriodFacts(periods.get("antar", maha), PERIOD_END)
    return facts_from_longitudes(
        lons,
        retrograde=retro,
        ascendant=SIGNS.index(lagna) * 30 + 15 if lagna else None,
        basis=basis,
        periods=period_facts,
    )
