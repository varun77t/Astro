from datetime import datetime, timedelta

import pytest

from app.engine.chart import compute_chart
from app.engine.constants import SIGNS, sign_index
from app.engine.ephemeris import ascendant_longitude
from app.engine.time_utils import resolve_birth_time

BANGALORE = {"tz_name": "Asia/Kolkata", "lat": 12.9716, "lon": 77.5946}


def first_minute_of_ascendant(sign: str, start: datetime) -> datetime:
    """Walk forward minute by minute until the ascendant enters `sign`."""
    local = start
    for _ in range(240):
        jd = resolve_birth_time(local, BANGALORE["tz_name"]).jd_ut
        if SIGNS[sign_index(ascendant_longitude(jd, BANGALORE["lat"], BANGALORE["lon"]))] == sign:
            return local
        local += timedelta(minutes=1)
    raise AssertionError("sign not reached")


@pytest.fixture(scope="module")
def virgo_rises():
    return first_minute_of_ascendant("Virgo", datetime(1990, 5, 17, 13, 30))


def test_exact_time_mid_sign_is_reliable():
    r = compute_chart(datetime(1990, 5, 17, 15, 30), **BANGALORE).reliability
    assert r.ascendant_reliable and r.basis == "ascendant"
    assert r.ascendant_signs == ["Virgo"]
    assert r.warnings == []


def test_exact_time_near_boundary_warns_but_keeps_ascendant(virgo_rises):
    r = compute_chart(virgo_rises + timedelta(minutes=2), **BANGALORE).reliability
    assert r.ascendant_signs == ["Leo", "Virgo"]
    assert not r.ascendant_reliable
    assert r.basis == "ascendant"
    assert "sign boundary" in r.warnings[0]


def test_approximate_time_across_boundary_uses_moon(virgo_rises):
    chart = compute_chart(virgo_rises, **BANGALORE, time_accuracy="approximate", window_minutes=60)
    assert chart.reliability.basis == "moon"
    assert "Leo or Virgo" in chart.reliability.warnings[0]


def test_unknown_time():
    r = compute_chart(
        datetime(1990, 5, 17, 12), **BANGALORE, time_accuracy="unknown", window_minutes=720
    ).reliability
    assert r.basis == "moon"
    assert not r.ascendant_reliable
    assert sorted(r.ascendant_signs) == sorted(SIGNS)  # 24 h covers every rising sign
    assert "Moon sign" in r.warnings[0]


def test_moon_sign_change_during_unknown_day_is_flagged():
    day = datetime(2024, 1, 1, 12)
    for _ in range(5):
        r = compute_chart(day, **BANGALORE, time_accuracy="unknown", window_minutes=720).reliability
        if not r.moon_sign_reliable:
            break
        day += timedelta(days=1)
    assert len(r.moon_signs) == 2
    assert any("Moon changed sign" in w for w in r.warnings)


def test_house_from_moon():
    chart = compute_chart(datetime(1990, 5, 17, 14, 35), **BANGALORE)
    assert chart.planet("Moon").house_from_moon == 1
    for p in chart.planets:
        expected = (SIGNS.index(p.sign) - SIGNS.index(chart.planet("Moon").sign)) % 12 + 1
        assert p.house_from_moon == expected


def test_navamsa_ascendant_straddles_a_sign_boundary(virgo_rises):
    # A sign boundary is also a navamsa boundary: Leo's last navamsa is Sagittarius, Virgo's first
    # is Capricorn.
    r = compute_chart(virgo_rises + timedelta(minutes=2), **BANGALORE).reliability
    assert r.navamsa_ascendant_signs == ["Sagittarius", "Capricorn"]
    assert not r.navamsa_ascendant_reliable


def test_navamsa_unknown_time_is_never_reliable():
    r = compute_chart(
        datetime(1990, 5, 17, 12, 0), **BANGALORE, time_accuracy="unknown", window_minutes=720
    ).reliability
    assert not r.navamsa_ascendant_reliable
    assert len(r.navamsa_ascendant_signs) == 12
    # The Moon crosses about 4 navamsas in a day.
    assert not r.navamsa_moon_reliable and len(r.navamsa_moon_signs) >= 3
