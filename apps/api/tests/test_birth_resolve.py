from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BANGALORE = {"tz_name": "Asia/Kolkata", "lat": 12.9716, "lon": 77.5946}
MUMBAI = {"tz_name": "Asia/Kolkata", "lat": 19.076, "lon": 72.8777}
NEW_YORK = {"tz_name": "America/New_York", "lat": 40.71, "lon": -74.0}


def resolve(**body):
    return client.post("/api/v1/birth/resolve", json=body)


def test_modern_ist():
    res = resolve(date="1990-05-17", time="14:35", **BANGALORE)
    assert res.status_code == 200
    body = res.json()
    assert body["utc"] == "1990-05-17T09:05:00Z"
    assert body["utc_offset"] == "+05:30"
    assert body["tz_abbreviation"] == "IST"
    assert body["is_dst"] is False
    assert body["notes"] == []
    assert body["window_minutes"] == 5


def test_wartime_india_has_notes():
    body = resolve(date="1943-06-01", time="12:00", **MUMBAI).json()
    assert body["utc_offset"] == "+06:30"
    assert body["is_dst"] is False  # war time, not daylight saving
    assert body["tz_abbreviation"] is None  # tzdata's "+0630" placeholder is dropped
    assert not any("Daylight saving" in n for n in body["notes"])
    assert any("World War II" in n for n in body["notes"])


def test_offset_override_for_bombay_time():
    body = resolve(date="1950-03-01", time="10:00", utc_offset_minutes=291, **MUMBAI).json()
    assert body["utc_offset"] == "+04:51"
    assert body["utc"] == "1950-03-01T05:09:00Z"
    assert body["offset_overridden"] is True
    assert body["tz_abbreviation"] is None


def test_dst_is_flagged():
    body = resolve(date="2021-07-04", time="12:00", **NEW_YORK).json()
    assert body["is_dst"] is True
    assert body["tz_abbreviation"] == "EDT"
    assert any("Daylight saving" in n for n in body["notes"])


def test_unknown_time_assumes_noon():
    body = resolve(date="1990-05-17", time_accuracy="unknown", **BANGALORE).json()
    assert body["time_assumed"] is True
    assert body["local_time"].startswith("1990-05-17T12:00:00")
    assert body["window_minutes"] == 720


def test_approximate_window_default_and_custom():
    base = {"date": "1990-05-17", "time": "14:35", "time_accuracy": "approximate", **BANGALORE}
    assert resolve(**base).json()["window_minutes"] == 30
    assert resolve(**base, time_window_minutes=90).json()["window_minutes"] == 90


def test_validation_errors():
    assert resolve(date="1990-05-17", **BANGALORE).status_code == 422  # exact needs a time
    assert resolve(date="1700-01-01", time="12:00", **BANGALORE).status_code == 422
    assert (
        resolve(date="1990-05-17", time="12:00", **{**BANGALORE, "tz_name": "Nowhere"}).json()[
            "detail"
        ]["code"]
        == "invalid_birth_time"
    )


def test_ambiguous_and_nonexistent():
    ambiguous = resolve(date="2021-11-07", time="01:30", **NEW_YORK)
    assert ambiguous.json()["detail"]["code"] == "ambiguous_local_time"
    chosen = resolve(date="2021-11-07", time="01:30", fold=1, **NEW_YORK).json()
    assert chosen["utc"] == "2021-11-07T06:30:00Z"
    missing = resolve(date="2021-03-14", time="02:30", **NEW_YORK)
    assert missing.json()["detail"]["code"] == "invalid_birth_time"
