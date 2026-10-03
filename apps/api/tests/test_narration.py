import json
from datetime import UTC, date, datetime, time

import pytest
from fastapi.testclient import TestClient

from app.interpret.narration_service import Narrator
from app.interpret.prompt_builder import build_messages, build_payload, input_hash
from app.interpret.reading_service import compute_readings_with_facts
from app.interpret.validator import validate
from app.llm.cache import ReadingCache
from app.llm.router import LLMRouter
from app.main import app
from app.schemas.birth import BirthInput
from tests.test_llm_router import FakeProvider

AS_OF = datetime(2026, 10, 3, tzinfo=UTC)
# Virgo Lagna. Venus exalted in Pisces (7th); Jupiter in Gemini (10th); Saturn, the Moon and
# Rahu in Capricorn (5th); Mercury in Aries (8th). Jupiter main period until May 2029.
BENGALURU = BirthInput(
    date=date(1990, 5, 17), time=time(14, 35), tz_name="Asia/Kolkata", lat=12.966667, lon=77.583333
)


@pytest.fixture(scope="module")
def relationships():
    readings, facts = compute_readings_with_facts(BENGALURU, AS_OF, areas=("relationships",))
    return readings.readings[0], facts


def good_answer(reading, **overrides) -> dict:
    """A reply that covers every rule and claims nothing the chart doesn't have."""
    answer = {
        "summary": "Partnership is a strong theme in your chart.",
        "strengths": [{"text": s.text, "rule_ids": [s.rule_id]} for s in reading.strengths],
        "watch_points": [{"text": s.text, "rule_ids": [s.rule_id]} for s in reading.watch_points],
        "current_period_note": (
            {
                "text": "Your Jupiter period puts partnership in focus.",
                "rule_ids": [s.rule_id for s in reading.current_period],
            }
            if reading.current_period
            else None
        ),
    }
    answer.update(overrides)
    return answer


def check(reading, facts, answer):
    text = answer if isinstance(answer, str) else json.dumps(answer)
    return validate(text, reading, facts)


# ------------------------------------------------------------------------------ validator


def test_a_faithful_answer_passes(relationships):
    reading, facts = relationships
    out, errors = check(reading, facts, good_answer(reading))
    assert errors == [] and out is not None


def test_correct_placements_and_fenced_json_pass(relationships):
    reading, facts = relationships
    summary = (
        "Venus is exalted in Pisces and sits in your 7th house. Your Lagna is Virgo, and "
        "Jupiter, ruler of your 7th house, is in your 10th house."
    )
    fenced = "```json\n" + json.dumps(good_answer(reading, summary=summary)) + "\n```"
    out, errors = check(reading, facts, fenced)
    assert errors == []


@pytest.mark.parametrize(
    ("summary", "expected"),
    [
        ("Venus is in your 5th house.", "says Venus is in the 5 house; it is in the 7"),
        ("Saturn rules your 7th house.", "says Saturn rules house 7; Jupiter does"),
        ("Jupiter is in Leo.", "says Jupiter is in Leo; it is in Gemini"),
        ("Mars is exalted, which helps.", "says Mars is exalted"),
        ("Your Lagna is Leo.", "says the Lagna is Leo; it is Virgo"),
        ("Your 7th house is Aries.", "says the 7 house is Aries; it is Pisces"),
        ("You have Kemadruma yoga.", "names Kemadruma yoga"),
        ("You will definitely marry young.", "no certainty"),
        ("Marriage brings an accident.", "no predicting a specific harm"),
        ("Venus sits at 12° of Pisces.", "uses degrees"),
    ],
)
def test_invented_or_forbidden_claims_are_rejected(relationships, summary, expected):
    reading, facts = relationships
    out, errors = check(reading, facts, good_answer(reading, summary=summary))
    assert out is None
    assert any(expected in e for e in errors), errors


def test_citations_must_be_given_complete_and_in_the_right_list(relationships):
    reading, facts = relationships
    assert reading.watch_points, "the reference chart should have a watch point"
    hard = reading.watch_points[0].rule_id

    dropped = good_answer(reading, watch_points=[])
    _, errors = check(reading, facts, dropped)
    assert any(f"watch_points leaves out {hard}" in e for e in errors)

    moved = good_answer(reading)
    moved["strengths"][0]["rule_ids"].append(hard)
    _, errors = check(reading, facts, moved)
    assert any(f"cites {hard}, which isn't one of the strengths rules" in e for e in errors)

    invented = good_answer(reading)
    invented["strengths"][0]["rule_ids"] = ["REL-MADE-UP"]
    _, errors = check(reading, facts, invented)
    assert any("REL-MADE-UP" in e for e in errors)


@pytest.mark.parametrize("reply", ["Sure! Here is your reading.", "{not json}", '{"summary": ""}'])
def test_malformed_replies_are_rejected(relationships, reply):
    reading, facts = relationships
    out, errors = check(reading, facts, reply)
    assert out is None and errors


# ------------------------------------------------------------------------------- prompt


def test_prompt_carries_chart_facts_only(relationships):
    reading, facts = relationships
    payload = build_payload(reading, facts, "en", "v1")
    blob = " ".join(m["content"] for m in build_messages(payload))
    for personal in ("1990", "14:35", "Bengaluru", "12.96", "77.58", "Asia/Kolkata"):
        assert personal not in blob
    assert '"lagna":"Virgo"' in blob
    assert reading.watch_points[0].rule_id in blob


def test_cache_key_is_stable_and_versioned(relationships):
    reading, facts = relationships
    a = input_hash(build_payload(reading, facts, "en", "v1"))
    assert a == input_hash(build_payload(reading, facts, "en", "v1"))
    assert a != input_hash(build_payload(reading, facts, "en", "v2"))


# ----------------------------------------------------------------------------- narrator


def _narrator(script):
    provider = FakeProvider("fake", script)
    return Narrator(LLMRouter([provider]), ReadingCache(":memory:")), provider


def test_narrates_validates_and_caches(relationships):
    reading, _ = relationships
    narrator, provider = _narrator([json.dumps(good_answer(reading))])
    first = narrator.narrate(BENGALURU, "relationships", AS_OF)
    assert (first.mode, first.provider, first.cached) == ("llm", "fake", False)
    assert first.summary == "Partnership is a strong theme in your chart."
    second = narrator.narrate(BENGALURU, "relationships", AS_OF)
    assert second.cached and second.summary == first.summary
    assert len(provider.calls) == 1  # the second visit never reached a provider


def test_a_bad_answer_is_retried_then_falls_back_to_rules(relationships):
    reading, _ = relationships
    bad = json.dumps(good_answer(reading, summary="Venus is in your 2nd house."))
    narrator, provider = _narrator([bad, bad])
    out = narrator.narrate(BENGALURU, "relationships", AS_OF)
    assert out.mode == "rules" and out.provider is None
    assert out.summary == reading.summary
    assert [p.rule_ids for p in out.watch_points] == [[s.rule_id] for s in reading.watch_points]
    assert len(provider.calls) == 2
    assert "says Venus is in the 2 house" in provider.calls[1][-1]["content"]


def test_without_providers_the_rules_are_shown():
    out = Narrator(None, None).narrate(BENGALURU, "career", AS_OF)
    assert out.mode == "rules" and out.reading.area == "career"


def test_api_narration_endpoint(relationships):
    reading, _ = relationships
    body = {
        "date": "1990-05-17",
        "time": "14:35",
        "tz_name": "Asia/Kolkata",
        "lat": 12.966667,
        "lon": 77.583333,
        "as_of": "2026-10-03T00:00:00Z",
    }
    with TestClient(app) as client:
        # No providers in tests: the rule texts come back.
        plain = client.post("/api/v1/readings/relationships/narration", json=body).json()
        assert plain["mode"] == "rules"
        app.state.narrator, _ = _narrator([json.dumps(good_answer(reading))])
        told = client.post("/api/v1/readings/relationships/narration", json=body).json()
        bad = client.post("/api/v1/readings/romance/narration", json=body)
    assert told["mode"] == "llm" and told["reading"]["area"] == "relationships"
    assert bad.status_code == 422


def test_typographic_hyphens_dont_hide_a_known_yoga():
    readings, facts = compute_readings_with_facts(BENGALURU, AS_OF, areas=("career",))
    yogas = {"dharma karma"}
    from app.interpret.validator import fact_errors

    assert fact_errors("Dharma\u2011Karma yoga lifts you.", facts, yogas) == []
    assert fact_errors("Kemadruma yoga holds you back.", facts, yogas)


def test_house_numbers_in_words_are_checked_too():
    from app.interpret.validator import fact_errors

    readings, facts = compute_readings_with_facts(BENGALURU, AS_OF, areas=("relationships",))
    assert fact_errors("Venus in the seventh house warms things.", facts, set()) == []
    assert fact_errors("Venus in the fifth house warms things.", facts, set())
