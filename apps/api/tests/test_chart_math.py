"""Pure-math pieces: signs, nakshatras, navamsa, houses, dignity, combustion."""

import pytest

from app.engine.constants import NAKSHATRA_SPAN, SIGNS, sign_index
from app.engine.houses import house_lord, house_sign, whole_sign_house
from app.engine.nakshatra import nakshatra_of
from app.engine.strength import dignity, is_combust
from app.engine.vargas import navamsa_sign_index


@pytest.mark.parametrize(
    ("lon", "sign"),
    [
        (0, "Aries"),
        (29.999999, "Aries"),
        (30, "Taurus"),
        (359.9999, "Pisces"),
        (360, "Aries"),
        (-0.5, "Pisces"),
        (725, "Aries"),
    ],
)
def test_sign_boundaries(lon, sign):
    assert SIGNS[sign_index(lon)] == sign


@pytest.mark.parametrize(
    ("lon", "name", "pada", "lord"),
    [
        (0.0, "Ashwini", 1, "Ketu"),
        (3.34, "Ashwini", 2, "Ketu"),
        (13.3333, "Ashwini", 4, "Ketu"),
        (NAKSHATRA_SPAN, "Bharani", 1, "Venus"),
        (45.2, "Rohini", 2, "Moon"),
        (98.0, "Pushya", 2, "Saturn"),
        (112.4, "Ashlesha", 2, "Mercury"),
        (359.99, "Revati", 4, "Mercury"),
    ],
)
def test_nakshatra(lon, name, pada, lord):
    n = nakshatra_of(lon)
    assert (n.name, n.pada, n.lord) == (name, pada, lord)


@pytest.mark.parametrize(
    ("sign", "first_navamsa"),
    [
        # Movable signs start from themselves, fixed from the 9th, dual from the 5th.
        ("Aries", "Aries"),
        ("Taurus", "Capricorn"),
        ("Gemini", "Libra"),
        ("Cancer", "Cancer"),
        ("Leo", "Aries"),
        ("Virgo", "Capricorn"),
        ("Libra", "Libra"),
        ("Scorpio", "Cancer"),
        ("Sagittarius", "Aries"),
        ("Capricorn", "Capricorn"),
        ("Aquarius", "Libra"),
        ("Pisces", "Cancer"),
    ],
)
def test_navamsa_first_part_of_each_sign(sign, first_navamsa):
    start = SIGNS.index(sign) * 30
    assert SIGNS[navamsa_sign_index(start + 1)] == first_navamsa
    # The ninth navamsa of a sign is 8 signs further on.
    assert navamsa_sign_index(start + 29) == (SIGNS.index(first_navamsa) + 8) % 12


def test_vargottama_example():
    # 15° Aries is the 5th navamsa of Aries -> Leo.
    assert SIGNS[navamsa_sign_index(15.0)] == "Leo"


def test_whole_sign_houses():
    cancer = SIGNS.index("Cancer")
    assert whole_sign_house(cancer, cancer) == 1
    assert whole_sign_house(SIGNS.index("Gemini"), cancer) == 12
    assert whole_sign_house(SIGNS.index("Scorpio"), cancer) == 5
    assert house_sign(5, cancer) == "Scorpio"
    assert house_lord(5, cancer) == "Mars"
    assert house_lord(1, SIGNS.index("Aquarius")) == "Saturn"


@pytest.mark.parametrize(
    ("planet", "lon", "expected"),
    [
        ("Sun", 10, "exalted"),  # Aries
        ("Sun", 190, "debilitated"),  # Libra
        ("Sun", 125, "moolatrikona"),  # Leo 5°
        ("Sun", 145, "own"),  # Leo 25°
        ("Sun", 100, "friendly"),  # Cancer (Moon)
        ("Sun", 75, "neutral"),  # Gemini (Mercury)
        ("Sun", 290, "enemy"),  # Capricorn (Saturn)
        ("Moon", 45.2, "exalted"),  # anywhere in Taurus counts as exalted
        ("Moon", 215, "debilitated"),  # Scorpio
        ("Mars", 5, "moolatrikona"),
        ("Mars", 20, "own"),
        ("Mercury", 160, "exalted"),  # Virgo
        ("Jupiter", 95, "exalted"),  # Cancer
        ("Jupiter", 280, "debilitated"),  # Capricorn
        ("Venus", 340, "exalted"),  # Pisces
        ("Saturn", 190, "exalted"),  # Libra
        ("Saturn", 310, "moolatrikona"),  # Aquarius 10°
        ("Rahu", 40, "exalted"),
        ("Ketu", 40, "debilitated"),
        ("Rahu", 100, None),
    ],
)
def test_dignity(planet, lon, expected):
    assert dignity(planet, lon) == expected


def test_combustion():
    assert is_combust("Mercury", 113, 100, retrograde=False)  # 13° < 14°
    assert not is_combust("Mercury", 113, 100, retrograde=True)  # retro orb is 12°
    assert is_combust("Venus", 355, 2, retrograde=False)  # 7° across 0° Aries
    assert not is_combust("Saturn", 120, 100, retrograde=False)
    assert not is_combust("Sun", 100, 100, retrograde=False)
    assert not is_combust("Rahu", 100, 100, retrograde=True)
