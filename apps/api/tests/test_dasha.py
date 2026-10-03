import json
from datetime import UTC, date, datetime, timedelta

import pytest

from app.engine.dasha import DASHA_YEARS, YEAR_DAYS, lords_from, running_at, subdivide, vimshottari
from app.engine.time_utils import resolve_birth_time
from tests.test_golden_charts import GOLDEN_FILES, parse_longitude

BIRTH = datetime(1990, 5, 17, 9, 5, tzinfo=UTC)


def test_years_add_up_to_120():
    assert sum(DASHA_YEARS.values()) == 120


def test_order_starts_from_the_birth_lord():
    assert lords_from("Mars") == [
        "Mars",
        "Rahu",
        "Jupiter",
        "Saturn",
        "Mercury",
        "Ketu",
        "Venus",
        "Sun",
        "Moon",
    ]


def test_moon_at_the_start_of_ashwini_gives_the_full_ketu_dasha():
    seq = vimshottari(0.0, BIRTH)
    assert seq.first_lord == "Ketu"
    assert seq.balance_years == pytest.approx(7)
    assert seq.epoch == BIRTH


def test_halfway_through_a_nakshatra_leaves_half_the_dasha():
    # Bharani (Venus, 20 years) spans 13°20' to 26°40'; its midpoint leaves 10 years.
    seq = vimshottari(20.0, BIRTH)
    assert seq.first_lord == "Venus"
    assert seq.balance_years == pytest.approx(10)
    assert seq.mahadashas[0].end - BIRTH == timedelta(days=10 * YEAR_DAYS)


def test_periods_tile_without_gaps():
    seq = vimshottari(123.4, BIRTH)
    mds = seq.mahadashas
    assert all(a.end == b.start for a, b in zip(mds, mds[1:], strict=False))
    assert mds[-1].end - mds[0].start == timedelta(days=120 * YEAR_DAYS)
    for md in mds:
        assert md.children[0].lord == md.lord
        assert md.children[0].start == md.start and md.children[-1].end == md.end
        assert all(a.end == b.start for a, b in zip(md.children, md.children[1:], strict=False))


def test_antardasha_lengths_are_proportional():
    start = BIRTH
    end = start + timedelta(days=20 * YEAR_DAYS)  # a Venus mahadasha
    ads = subdivide("Venus", start, end)
    venus_venus = ads[0].end - ads[0].start
    assert venus_venus.days == pytest.approx(20 * 20 / 120 * YEAR_DAYS, abs=1)  # 3 y 4 m


def test_running_at():
    seq = vimshottari(20.0, BIRTH)
    assert running_at(seq.mahadashas, BIRTH).lord == "Venus"
    assert running_at(seq.mahadashas, BIRTH + timedelta(days=11 * YEAR_DAYS)).lord == "Sun"


# --- against the reference software ---------------------------------------------------------

DASHA_CASES = [p for p in GOLDEN_FILES if "dasha" in json.loads(p.read_text(encoding="utf-8"))]

# AstroSage adds calendar years and months rather than 365.25-day years, which moves a
# boundary by up to a day or two; anything more would be a real arithmetic difference.
TOLERANCE_DAYS = 2


def _birth_utc(case) -> datetime:
    b = case["birth"]
    local = datetime.fromisoformat(f"{b['date']}T{b['time']}")
    return resolve_birth_time(local, b["tz_name"]).utc


@pytest.mark.parametrize("path", DASHA_CASES, ids=lambda p: p.stem)
def test_mahadashas_match_reference(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    ref = case["dasha"]
    seq = vimshottari(parse_longitude(ref["reference_moon"]), _birth_utc(case))
    errors = []
    for md, (lord, end) in zip(seq.mahadashas, ref["mahadasha_ends"], strict=True):
        diff = abs((md.end.date() - date.fromisoformat(end)).days)
        if md.lord != lord or diff > TOLERANCE_DAYS:
            errors.append(f"{md.lord} ends {md.end.date()} vs {lord} {end}")
    assert not errors, "; ".join(errors)


def test_antardashas_match_reference():
    path = next(p for p in DASHA_CASES if p.stem == "newyork-1979")
    case = json.loads(path.read_text(encoding="utf-8"))
    seq = vimshottari(parse_longitude(case["dasha"]["reference_moon"]), _birth_utc(case))
    for md_lord, ends in case["dasha"]["antardasha_ends"].items():
        md = next(m for m in seq.mahadashas if m.lord == md_lord)
        for ad, (lord, end) in zip(md.children, ends, strict=True):
            assert ad.lord == lord
            assert abs((ad.end.date() - date.fromisoformat(end)).days) <= TOLERANCE_DAYS, (
                f"{md_lord}-{lord}"
            )


# --- API --------------------------------------------------------------------------------------

BENGALURU = {
    "date": "1990-05-17",
    "time": "14:35",
    "tz_name": "Asia/Kolkata",
    "lat": 12.9667,
    "lon": 77.5833,
}


def _post(body):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        return client.post("/api/v1/dasha", json=body)


def test_api_current_period():
    res = _post({**BENGALURU, "as_of": "2026-10-03T00:00:00Z"})
    assert res.status_code == 200
    body = res.json()
    assert body["first_lord"] == "Mars"
    assert len(body["mahadashas"]) == 9 and all(
        len(m["antardashas"]) == 9 for m in body["mahadashas"]
    )
    # AstroSage: Jupiter mahadasha from 20 May 2013 to 20 May 2029.
    assert body["current"]["mahadasha"]["lord"] == "Jupiter"
    assert len(body["pratyantardashas"]) == 9
    # +-5 minutes moves the Moon ~2.7 arcminutes, which slides a 7-year Mars dasha ~8.6 days.
    assert body["timing_reliable"] and 5 < body["uncertainty_days"] < 15


def test_api_unknown_time_widens_the_dates():
    body = _post({**BENGALURU, "time": None, "time_accuracy": "unknown"}).json()
    # Over +-12 hours the Moon crosses ~6.5°; either the order changes or dates move by years.
    assert not body["timing_reliable"] or body["uncertainty_days"] > 365


def test_api_before_birth_has_no_current_period():
    body = _post({**BENGALURU, "as_of": "1980-01-01T00:00:00Z"}).json()
    assert body["current"] is None and body["pratyantardashas"] == []
