"""Whole-chart invariants and the /chart endpoint."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.engine.chart import compute_chart
from app.engine.constants import PLANETS, SIGN_LORDS
from app.main import app

client = TestClient(app)

BANGALORE = {"tz_name": "Asia/Kolkata", "lat": 12.9716, "lon": 77.5946}


@pytest.fixture(scope="module")
def chart():
    return compute_chart(datetime(1990, 5, 17, 14, 35), **BANGALORE)


def test_meta(chart):
    assert chart.meta.ayanamsa == "lahiri"
    assert chart.meta.node_type == "mean"
    assert chart.meta.utc_offset == "+05:30"
    assert chart.meta.utc.isoformat() == "1990-05-17T09:05:00+00:00"


def test_planets_complete_and_consistent(chart):
    assert [p.name for p in chart.planets] == PLANETS
    for p in chart.planets:
        assert 1 <= p.house <= 12
        assert 1 <= p.pada <= 4
        assert 0 <= p.degree_in_sign < 30
        assert p.sign_lord == SIGN_LORDS[p.sign]
    rahu, ketu = chart.planet("Rahu"), chart.planet("Ketu")
    assert (ketu.house - rahu.house) % 12 == 6


def test_houses(chart):
    assert [h.house for h in chart.houses] == list(range(1, 13))
    assert chart.houses[0].sign == chart.ascendant.sign
    occupants = sorted(name for h in chart.houses for name in h.occupants)
    assert occupants == sorted(PLANETS)
    for h in chart.houses:
        assert h.lord == SIGN_LORDS[h.sign]
        assert h.lord_house == chart.planet(h.lord).house


def test_d9(chart):
    d9 = chart.divisional["D9"]
    assert [p.name for p in d9.planets] == PLANETS
    assert all(1 <= p.house <= 12 for p in d9.planets)


def test_endpoint_returns_chart():
    res = client.post("/api/v1/chart", json={"date": "1990-05-17", "time": "14:35:00", **BANGALORE})
    assert res.status_code == 200
    body = res.json()
    assert body["meta"]["utc_offset"] == "+05:30"
    assert len(body["planets"]) == 9


def test_endpoint_ambiguous_time():
    res = client.post(
        "/api/v1/chart",
        json={
            "date": "2021-11-07",
            "time": "01:30",
            "tz_name": "America/New_York",
            "lat": 40.71,
            "lon": -74.0,
        },
    )
    assert res.status_code == 422
    assert res.json()["detail"]["code"] == "ambiguous_local_time"
    assert len(res.json()["detail"]["options_utc"]) == 2


def test_endpoint_nonexistent_time():
    res = client.post(
        "/api/v1/chart",
        json={
            "date": "2021-03-14",
            "time": "02:30",
            "tz_name": "America/New_York",
            "lat": 40.71,
            "lon": -74.0,
        },
    )
    assert res.status_code == 422
    assert res.json()["detail"]["code"] == "invalid_birth_time"


def test_endpoint_validates_coordinates():
    res = client.post(
        "/api/v1/chart",
        json={
            "date": "1990-05-17",
            "time": "14:35",
            "tz_name": "Asia/Kolkata",
            "lat": 120,
            "lon": 77.6,
        },
    )
    assert res.status_code == 422
