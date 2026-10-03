"""Sanity checks against astronomical events whose geometry is independently known.

These don't replace golden charts from reference software (tests/test_golden_charts.py),
but they catch wiring mistakes: wrong flags, wrong ayanamsa, tropical/sidereal mix-ups.
"""

from datetime import UTC, datetime

import pytest
import swisseph as swe

from app.engine.constants import SIGNS, sign_index
from app.engine.ephemeris import ascendant_longitude, ayanamsa, body_positions
from app.engine.nakshatra import nakshatra_of
from app.engine.strength import angular_distance
from app.engine.time_utils import julian_day_ut


def jd(*args) -> float:
    return julian_day_ut(datetime(*args, tzinfo=UTC))


def positions(*args) -> dict:
    return {b.name: b for b in body_positions(jd(*args))}


def test_lahiri_ayanamsa_at_j2000():
    # Lahiri is ~23°51' at J2000 and grows ~50.3"/year.
    assert ayanamsa(2451545.0) == pytest.approx(23.853, abs=0.01)
    assert ayanamsa(jd(2024, 1, 1)) - ayanamsa(jd(2000, 1, 1)) == pytest.approx(
        24 * 50.29 / 3600, abs=0.01
    )


def test_tropical_sun_at_march_equinox_2024():
    # Equinox: 2024-03-20 03:06 UTC, tropical Sun at 0° Aries.
    lon = swe.calc_ut(jd(2024, 3, 20, 3, 6), swe.SUN, swe.FLG_MOSEPH)[0][0]
    assert angular_distance(lon, 0.0) < 0.01


def test_mesha_sankranti_2024():
    # Sidereal Sun enters Aries on 2024-04-13 (about 15:45 UTC).
    assert SIGNS[sign_index(positions(2024, 4, 12, 12)["Sun"].longitude)] == "Pisces"
    assert SIGNS[sign_index(positions(2024, 4, 14, 12)["Sun"].longitude)] == "Aries"


def test_total_solar_eclipse_2024_04_08():
    # New moon 18:21 UTC: Sun and Moon conjunct, sidereal Pisces in Revati.
    p = positions(2024, 4, 8, 18, 21)
    assert angular_distance(p["Sun"].longitude, p["Moon"].longitude) < 0.1
    assert SIGNS[sign_index(p["Sun"].longitude)] == "Pisces"
    assert nakshatra_of(p["Sun"].longitude).name == "Revati"


def test_great_conjunction_2020_12_21():
    # Jupiter and Saturn ~0.1° apart, tropical 0° Aquarius -> sidereal Capricorn.
    p = positions(2020, 12, 21, 18)
    assert angular_distance(p["Jupiter"].longitude, p["Saturn"].longitude) < 0.2
    assert SIGNS[sign_index(p["Jupiter"].longitude)] == "Capricorn"


def test_mercury_retrograde_april_2024():
    # Mercury was retrograde 2024-04-01 .. 2024-04-25.
    assert positions(2024, 4, 10)["Mercury"].retrograde
    assert not positions(2024, 5, 10)["Mercury"].retrograde


@pytest.mark.parametrize("year", [1950, 1985, 2000, 2024])
def test_nodes(year):
    p = positions(year, 6, 1)
    assert p["Rahu"].retrograde and p["Ketu"].retrograde  # mean node always moves backwards
    assert angular_distance(p["Rahu"].longitude, p["Ketu"].longitude) == pytest.approx(180)
    assert not p["Sun"].retrograde and not p["Moon"].retrograde


def test_all_longitudes_normalized():
    for body in body_positions(jd(1999, 12, 31, 23, 59)):
        assert 0 <= body.longitude < 360


def test_sidereal_ascendant_is_tropical_minus_ayanamsa():
    t = jd(1990, 5, 17, 9, 5)
    _, ascmc = swe.houses_ex(t, 12.9716, 77.5946, b"W")
    expected = (ascmc[0] - ayanamsa(t)) % 360
    assert angular_distance(ascendant_longitude(t, 12.9716, 77.5946), expected) < 1e-6


def test_ascendant_passes_through_every_sign_in_a_day():
    start = jd(2024, 6, 1)
    signs = {sign_index(ascendant_longitude(start + h / 24, 28.61, 77.21)) for h in range(24)}
    assert signs == set(range(12))


@pytest.mark.parametrize("lat", [-45.0, 0.0, 60.0])
def test_ascendant_at_varied_latitudes(lat):
    assert 0 <= ascendant_longitude(jd(2000, 1, 1), lat, 0.0) < 360
