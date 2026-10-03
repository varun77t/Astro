import pytest

from app.interpret.rule_matcher import RuleError, parse_condition
from tests.rule_charts import chart_from_spec


def holds(when, **spec):
    return parse_condition(when).eval(chart_from_spec(spec or {"lagna": "Aries"}))


def texts(result):
    return [b.text for b in result]


def test_planet_in_house_and_its_reason():
    r = holds({"planet": "Jupiter", "house": 5}, lagna="Aries", Jupiter="Leo")
    assert texts(r) == ["Jupiter is in your 5th house"]
    assert r[0].planets == ("Jupiter",) and r[0].houses == (5,)
    assert holds({"planet": "Jupiter", "house": 5}, lagna="Taurus", Jupiter="Leo") is None


def test_house_sets_and_lists():
    assert holds({"planet": "Jupiter", "house": "kendra"}, lagna="Aries", Jupiter="Cancer")
    assert holds({"planet": "Jupiter", "house": [6, "trikona"]}, lagna="Aries", Jupiter="Virgo")
    assert holds({"planet": "Jupiter", "house": "dusthana"}, lagna="Aries", Jupiter="Leo") is None


def test_lord_of_names_the_ruler():
    # Leo Lagna: Mars rules the 4th (Scorpio) and 9th (Aries).
    r = holds({"lord_of": 9, "dignity": "strong"}, lagna="Leo", Mars="Capricorn")
    assert texts(r) == ["Mars, ruler of your 9th house, is exalted"]
    r = holds({"lord_of": 10, "is": "Sun"}, lagna="Scorpio")
    assert texts(r) == ["The Sun rules your 10th house"]


def test_moon_basis_counts_from_the_moon_and_ignores_the_moon_itself():
    spec = {"basis": "moon", "Moon": "Cancer", "Jupiter": "Scorpio"}
    r = holds({"planet": "Jupiter", "house": 5}, **spec)
    assert texts(r) == ["Jupiter is in the 5th house from your Moon"]
    # The Moon is in the 1st from itself by definition; that says nothing about the chart.
    assert holds({"planet": "Moon", "house": 1}, **spec) is None
    assert holds({"house": 1, "has": "Moon"}, **spec) is None
    assert holds({"lagna": "Cancer"}, **spec) is None


def test_from_moon_on_an_ascendant_chart():
    r = holds(
        {"planet": "Jupiter", "from": "moon", "house": "kendra"},
        lagna="Aries",
        Moon="Aquarius",
        Jupiter="Taurus",
    )
    assert texts(r) == ["Jupiter is in the 4th house from your Moon"]


def test_conjunction_and_its_negation():
    spec = {"lagna": "Aries", "Sun": "Leo 10", "Mercury": "Leo 28"}
    assert texts(holds({"planet": "Mercury", "with": "Sun"}, **spec)) == [
        "Mercury sits with the Sun"
    ]
    assert holds({"planet": "Mercury", "not_with": "Sun"}, **spec) is None
    # 18° apart, outside the 14° orb; a "not combust" test holds but has nothing to say.
    assert holds({"planet": "Mercury", "combust": False}, **spec) == []


def test_aspects_are_whole_sign():
    # Saturn in Aries aspects the 3rd, 7th and 10th signs from it: Gemini, Libra, Capricorn.
    for house in (3, 7, 10):
        assert holds({"house": house, "aspected_by": "Saturn"}, lagna="Aries", Saturn="Aries")
    assert holds({"house": 5, "aspected_by": "Saturn"}, lagna="Aries", Saturn="Aries") is None
    # Nodes cast no aspects here.
    assert holds({"house": 7, "aspected_by": "Rahu"}, lagna="Aries", Rahu="Aries") is None


def test_the_moon_is_a_benefic_only_when_waxing():
    waxing = {"lagna": "Aries", "Sun": "Aries 1", "Moon": "Cancer 1", "Venus": "Taurus"}
    waning = {
        "lagna": "Aries",
        "Sun": "Aries 1",
        "Moon": "Capricorn 1",
        "Venus": "Taurus",
        "Mercury": "Gemini",
    }
    assert holds({"house": 4, "has": "benefic"}, **waxing)
    assert holds({"house": 10, "has": "benefic"}, **waning) is None
    assert holds({"house": 10, "has": "malefic"}, **waning)


def test_exchange():
    r = holds({"exchange": [5, 9]}, lagna="Aries", Sun="Sagittarius", Jupiter="Leo")
    assert texts(r) == [
        "The Sun and Jupiter, rulers of your 5th and 9th houses, sit in each other's signs"
    ]
    assert holds({"exchange": [5, 9]}, lagna="Aries", Sun="Sagittarius", Jupiter="Virgo") is None


def test_combinators():
    any_ = {"any": [{"planet": "Jupiter", "house": 1}, {"planet": "Venus", "house": 4}]}
    assert texts(holds(any_, lagna="Aries", Venus="Cancer")) == ["Venus is in your 4th house"]
    # `not` holds silently: it has nothing to point at.
    assert holds({"not": {"planet": "Jupiter", "house": 1}}, lagna="Aries") == []
    both = [{"planet": "Venus", "house": 4}, {"planet": "Saturn", "house": 2}]
    assert len(holds(both, lagna="Aries", Venus="Cancer")) == 2


def test_period_subject():
    r = holds({"period": "maha", "rules": [5, 9]}, lagna="Aries", period={"maha": "Jupiter"})
    assert texts(r) == ["Your Jupiter period runs until Jan 2030", "Jupiter rules your 9th house"]
    # No running period (before birth, after the cycle): period rules can't match.
    assert holds({"period": "maha"}, lagna="Aries") is None


@pytest.mark.parametrize(
    "bad",
    [
        {"planet": "Pluto", "house": 1},
        {"planet": "Jupiter", "house": 13},
        {"planet": "Jupiter", "colour": "red"},
        {"planet": "Jupiter", "lord_of": 5, "house": 1},
        {"planet": "Jupiter"},
        {"house": 5},
        {"house": [5, 6], "has": "Jupiter"},
        {"lagna": "Leo", "house": 1},
        {"any": []},
        {"planet": "Jupiter", "from": "sun", "house": 1},
        {"planet": "Jupiter", "dignity": "great"},
    ],
)
def test_malformed_conditions_fail_at_load_time(bad):
    with pytest.raises(RuleError):
        parse_condition(bad)
