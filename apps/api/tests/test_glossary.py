from fastapi.testclient import TestClient

from app.engine.constants import SIGNS
from app.knowledge.loader import load_glossary
from app.main import app

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
DIGNITIES = ["exalted", "moolatrikona", "own", "friendly", "neutral", "enemy", "debilitated"]


def test_every_chart_term_has_an_entry():
    ids = {e.id for e in load_glossary()}
    expected = (
        {f"planet.{p.lower()}" for p in PLANETS}
        | {f"sign.{s.lower()}" for s in SIGNS}
        | {f"house.{n}" for n in range(1, 13)}
        | {f"dignity.{d}" for d in DIGNITIES}
        | {
            "state.retrograde",
            "state.combust",
            "concept.lagna",
            "concept.navamsa",
            "concept.chandra_lagna",
            "concept.sign_boundary",
        }
    )
    assert expected <= ids, f"missing: {sorted(expected - ids)}"


def test_entries_stay_short():
    for e in load_glossary():
        assert len(e.short) <= 70, e.id
        assert len(e.body.split()) <= 70, e.id


def test_no_fear_words():
    banned = ("death", "die", "accident", "disease", "illness", "curse", "doom", "danger")
    for e in load_glossary():
        text = f"{e.short} {e.body}".lower()
        assert not any(f" {w}" in text for w in banned), e.id


def test_endpoint():
    with TestClient(app) as client:
        res = client.get("/api/v1/glossary")
    assert res.status_code == 200
    assert res.headers["cache-control"].startswith("public")
    venus = next(e for e in res.json()["entries"] if e["id"] == "planet.venus")
    assert venus["transliteration"] == "Shukra"
