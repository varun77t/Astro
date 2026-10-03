"""Compare the engine against charts produced by trusted reference software.

Fixtures live in data/golden_charts/*.json (files starting with "_" are ignored).
See data/golden_charts/README.md for how to collect them.
"""

import json
import re
from datetime import datetime
from pathlib import Path

import pytest

from app.engine.chart import compute_chart
from app.engine.constants import SIGNS
from app.engine.strength import angular_distance

GOLDEN_DIR = Path(__file__).resolve().parents[3] / "data" / "golden_charts"
GOLDEN_FILES = sorted(p for p in GOLDEN_DIR.glob("*.json") if not p.name.startswith("_"))

# Jagannatha Hora style abbreviations.
SIGN_ABBREVIATIONS = {
    "ar": "Aries",
    "ta": "Taurus",
    "ge": "Gemini",
    "cn": "Cancer",
    "le": "Leo",
    "vi": "Virgo",
    "li": "Libra",
    "sc": "Scorpio",
    "sg": "Sagittarius",
    "cp": "Capricorn",
    "aq": "Aquarius",
    "pi": "Pisces",
}
SIGN_FIRST = re.compile(r"^([A-Za-z]+)\s+(\d+)\s*[:°]\s*(\d+)(?:\s*[:']\s*([\d.]+))?\s*\"?$")
DEGREE_FIRST = re.compile(r"^(\d+)\s*°?\s*([A-Za-z]+)\s+(\d+)\s*'?\s*(?:([\d.]+)\s*\"?)?$")


def parse_sign(token: str) -> int:
    name = SIGN_ABBREVIATIONS.get(token.lower(), token.capitalize())
    if name not in SIGNS:
        raise ValueError(f"unknown sign {token!r}")
    return SIGNS.index(name)


def parse_longitude(value: float | str) -> float:
    """Accepts 45.2, "Taurus 15:12:00", "Taurus 15°12'00\"", or "15 Ta 12' 00.5\""."""
    if isinstance(value, int | float):
        return float(value)
    text = value.strip()
    if m := SIGN_FIRST.match(text):
        sign, d, mi, s = m.groups()
    elif m := DEGREE_FIRST.match(text):
        d, sign, mi, s = m.groups()
    else:
        raise ValueError(f"cannot parse longitude {value!r}")
    return parse_sign(sign) * 30 + int(d) + int(mi) / 60 + float(s or 0) / 3600


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Taurus 15:12:00", 45.2),
        ("Taurus 15°12'00\"", 45.2),
        ("15 Ta 12' 00\"", 45.2),
        ("15 Ta 12' 00.00\"", 45.2),
        ("Sg 1:30", 241.5),
        (123.25, 123.25),
    ],
)
def test_parse_longitude(text, expected):
    assert parse_longitude(text) == pytest.approx(expected)


@pytest.mark.skipif(not GOLDEN_FILES, reason=f"no golden charts yet in {GOLDEN_DIR}")
@pytest.mark.parametrize("path", GOLDEN_FILES, ids=lambda p: p.stem)
def test_golden_chart(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    birth = case["birth"]
    expected = case["expected"]
    tolerance = case.get("tolerance_arcmin", 1.0) / 60

    local = datetime.fromisoformat(f"{birth['date']}T{birth['time']}")
    chart = compute_chart(local, birth["tz_name"], birth["lat"], birth["lon"], birth.get("fold"))

    errors = []
    if (offset := birth.get("expected_utc_offset")) and chart.meta.utc_offset != offset:
        errors.append(f"UTC offset {chart.meta.utc_offset} != {offset}")
    asc_expected = parse_longitude(expected["ascendant"])
    if SIGNS[int(asc_expected // 30)] != chart.ascendant.sign:
        errors.append(f"ascendant sign {chart.ascendant.sign} != {SIGNS[int(asc_expected // 30)]}")
    asc_diff = angular_distance(asc_expected, chart.ascendant.longitude)
    if asc_diff > case.get("ascendant_tolerance_arcmin", 1.0) / 60:
        errors.append(f"ascendant off by {asc_diff * 60:.2f}'")

    for name, value in expected["planets"].items():
        diff = angular_distance(parse_longitude(value), chart.planet(name).longitude)
        if diff > tolerance:
            errors.append(f"{name} off by {diff * 60:.2f}'")

    for name, (nakshatra, pada) in expected.get("nakshatras", {}).items():
        p = chart.planet(name)
        if (p.nakshatra, p.pada) != (nakshatra, pada):
            errors.append(f"{name} nakshatra {p.nakshatra}-{p.pada} != {nakshatra}-{pada}")

    assert not errors, f"{path.name} ({case.get('source', 'unknown source')}): " + "; ".join(errors)
