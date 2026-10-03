import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.core.auth import verify_token
from app.core.quota import DailyQuota
from app.interpret.reading_service import compute_readings_with_facts
from app.main import app
from tests.test_llm_router import FakeClock
from tests.test_narration import AS_OF, BENGALURU, _narrator, good_answer


class FakeJWKS:
    """Stands in for the project's published signing keys."""

    def __init__(self, public_key):
        self.public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return type("Key", (), {"key": self.public_key})()


KEY = ec.generate_private_key(ec.SECP256R1())
OTHER = ec.generate_private_key(ec.SECP256R1())
JWKS = FakeJWKS(KEY.public_key())


def token(signer=KEY, **claims) -> str:
    body = {"sub": "user-1", "aud": "authenticated", "exp": int(time.time()) + 600, **claims}
    return jwt.encode(body, signer, algorithm="ES256")


def test_a_valid_token_names_the_user():
    assert verify_token(token(), JWKS) == "user-1"


@pytest.mark.parametrize(
    "bad",
    [
        token(exp=int(time.time()) - 10),  # expired
        token(aud="anon"),  # not a signed-in user's token
        token(signer=OTHER),  # signed by someone else
        "not.a.token",
    ],
)
def test_bad_tokens_are_refused(bad):
    assert verify_token(bad, JWKS) is None


def test_daily_quota_counts_and_resets_at_midnight_utc():
    clock = FakeClock(1_700_000_000.0)
    q = DailyQuota(clock)
    assert q.remaining("ip:1", 2) == 2
    q.spend("ip:1")
    q.spend("ip:1")
    assert q.remaining("ip:1", 2) == 0 and q.remaining("ip:2", 2) == 2
    clock.t += 86400
    assert q.remaining("ip:1", 2) == 2


@pytest.fixture(scope="module")
def reading():
    readings, _ = compute_readings_with_facts(BENGALURU, AS_OF, areas=("relationships",))
    return readings.readings[0]


BODY = {
    "date": "1990-05-17",
    "time": "14:35",
    "tz_name": "Asia/Kolkata",
    "lat": 12.966667,
    "lon": 77.583333,
    "as_of": "2026-10-03T00:00:00Z",
}


def test_fresh_ai_readings_are_limited_per_caller(reading):
    with TestClient(app) as client:
        app.state.narrator, provider = _narrator([json.dumps(good_answer(reading))] * 3)
        quota = app.state.narration_quota
        for _ in range(10):  # an anonymous visitor's whole day
            quota.spend("ip:testclient")
        res = client.post("/api/v1/readings/relationships/narration", json=BODY).json()
    assert res["mode"] == "rules" and res["limit_reached"] is True
    assert provider.calls == []


def test_cached_readings_are_free(reading):
    with TestClient(app) as client:
        app.state.narrator, provider = _narrator([json.dumps(good_answer(reading))])
        first = client.post("/api/v1/readings/relationships/narration", json=BODY).json()
        quota = app.state.narration_quota
        assert quota.remaining("ip:testclient", 10) == 9
        for _ in range(9):
            quota.spend("ip:testclient")
        again = client.post("/api/v1/readings/relationships/narration", json=BODY).json()
    assert first["mode"] == again["mode"] == "llm"
    assert again["cached"] is True and len(provider.calls) == 1
