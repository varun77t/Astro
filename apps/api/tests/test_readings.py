import json
from datetime import UTC, date, datetime, time

import pytest
from fastapi.testclient import TestClient

from app.interpret.guardrails import violations
from app.interpret.reading_service import compute_readings_for, sample_offsets
from app.knowledge.rules import load_rules
from app.main import app
from app.schemas.birth import BirthInput
from app.schemas.reading import AREAS
from tests.test_golden_charts import GOLDEN_FILES

AS_OF = datetime(2026, 10, 3, tzinfo=UTC)
# Virgo Lagna; Venus exalted in Pisces (7th), Saturn in Capricorn (5th) with the Moon,
# Jupiter in Gemini (10th); Jupiter mahadasha until May 2029.
BENGALURU = BirthInput(
    date=date(1990, 5, 17), time=time(14, 35), tz_name="Asia/Kolkata", lat=12.966667, lon=77.583333
)


def _all_statements(reading):
    return reading.strengths + reading.watch_points + reading.current_period


@pytest.fixture(scope="module")
def exact():
    return {r.area: r for r in compute_readings_for(BENGALURU, AS_OF).readings}


def test_sample_offsets_cover_the_window_edges():
    assert sample_offsets(5) == [-5, 5]
    offsets = sample_offsets(60)
    assert offsets[0] == -60 and offsets[-1] == 60 and 0 not in offsets
    assert len(sample_offsets(720)) == 144


def test_every_area_is_read(exact):
    assert list(exact) == list(AREAS)
    for r in exact.values():
        assert r.basis == "ascendant"
        assert r.summary
        assert len(r.strengths) <= 6 and len(r.watch_points) <= 4
        assert all(s.tone == "cautionary" for s in r.watch_points)
        for s in _all_statements(r):
            assert s.because, s.rule_id
            assert violations(s.text) == []
        if len(r.current_period) > 1:  # the "not tied to this area" fallback only stands alone
            assert not any(s.rule_id.endswith("DASHA-QUIET") for s in r.current_period)


def test_placements_known_from_the_reference_chart(exact):
    ids = {area: set(r.matched_rule_ids) for area, r in exact.items()}
    assert {"REL-7H-VEN", "REL-VEN-STRONG"} <= ids["relationships"]  # Venus exalted in the 7th
    assert {"EDU-5H-SAT", "EDU-MOON-SAT"} <= ids["education"]  # Saturn and Moon in the 5th
    assert "CAR-10H-JUP" in ids["career"]  # Jupiter in the 10th
    assert "CAR-FIELD-MER" in ids["career"]  # Gemini 10th, ruled by Mercury


def test_one_placement_is_not_said_twice(exact):
    for r in exact.values():
        reasons = [tuple(b.text for b in s.because) for s in r.strengths + r.watch_points]
        assert len(reasons) == len(set(reasons)), r.area
    # Jupiter in the 10th is both CAR-10H-JUP and Amala yoga; only one is shown.
    shown = {s.rule_id for s in exact["career"].strengths}
    assert len(shown & {"CAR-10H-JUP", "CAR-AMALA"}) == 1


def test_current_period(exact):
    rel = exact["relationships"].current_period
    assert rel[0].rule_id == "REL-DASHA-RULES-7"  # Jupiter rules Pisces, the 7th from Virgo
    assert rel[0].because[0].text == "Your Jupiter period runs until May 2029"
    assert rel[0].certainty == "sure"
    # Where the period doesn't touch an area, the quiet fallback says so.
    assert exact["money"].current_period[0].rule_id == "MON-DASHA-QUIET"


def test_exact_time_reading_is_sure_throughout(exact):
    for r in exact.values():
        assert all(s.certainty == "sure" for s in _all_statements(r)), r.area


def test_a_loose_time_counts_from_the_moon_and_marks_what_could_change():
    loose = BENGALURU.model_copy(update={"time": None, "time_accuracy": "unknown"})
    readings = compute_readings_for(loose, AS_OF).readings
    for r in readings:
        assert r.basis == "moon"
        assert not any(i.startswith("CAR-YOGAKARAKA") for i in r.matched_rule_ids)
        for s in r.strengths + r.watch_points:
            for b in s.because:
                assert "your 1st" not in b.text and " your 5th" not in b.text
    # The Moon enters Aquarius within the day, so house-from-Moon rules are only possible.
    statements = [s for r in readings for s in r.strengths + r.watch_points]
    assert any(s.certainty == "possible" for s in statements)
    # Venus is exalted all day long; that stays sure.
    venus = next(s for s in statements if s.rule_id == "REL-VEN-STRONG")
    assert venus.certainty == "sure"


@pytest.mark.parametrize("path", GOLDEN_FILES, ids=lambda p: p.stem)
def test_golden_charts_get_a_usable_reading(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    b = case["birth"]
    birth = BirthInput(
        date=date.fromisoformat(b["date"]),
        time=time.fromisoformat(b["time"]),
        tz_name=b["tz_name"],
        lat=b["lat"],
        lon=b["lon"],
    )
    readings = compute_readings_for(birth, AS_OF).readings
    rules = load_rules()
    for r in readings:
        natal = r.strengths + r.watch_points
        assert len(natal) <= 10 and len(r.matched_rule_ids) <= 25, (r.area, r.matched_rule_ids)
        if not natal:  # a chart can be unremarkable in one area; the summary must say so
            assert r.summary == rules[r.area].summary["quiet"]
        assert r.current_period, r.area
    assert sum(len(r.strengths + r.watch_points) for r in readings) >= 10


def _body(**extra):
    return {
        "date": "1990-05-17",
        "time": "14:35",
        "tz_name": "Asia/Kolkata",
        "lat": 12.966667,
        "lon": 77.583333,
        "as_of": "2026-10-03T00:00:00Z",
        **extra,
    }


def test_api_all_areas():
    with TestClient(app) as client:
        res = client.post("/api/v1/readings", json=_body())
    assert res.status_code == 200
    data = res.json()
    assert [r["area"] for r in data["readings"]] == list(AREAS)
    assert data["rules_version"] and data["note"]
    health = data["readings"][3]
    assert health["disclaimer"].startswith("Themes from tradition, not medical advice")


def test_api_one_area_and_bad_area():
    with TestClient(app) as client:
        one = client.post("/api/v1/readings/career", json=_body())
        bad = client.post("/api/v1/readings/astrology", json=_body())
    assert one.status_code == 200 and one.json()["area"] == "career"
    assert bad.status_code == 422
