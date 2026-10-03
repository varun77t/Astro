import httpx
import pytest

from app.llm.base import (
    AuthFailed,
    Completion,
    ProviderConfig,
    ProviderError,
    RateLimited,
)
from app.llm.openai_compat import OpenAICompatibleProvider
from app.llm.rate_limiter import RateLimiter
from app.llm.router import LLMRouter


class FakeClock:
    def __init__(self, t: float = 1_700_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


class FakeProvider:
    """Plays back a script: each item is a reply text or an exception to raise."""

    def __init__(self, name: str, script: list):
        self.name, self.model = name, f"{name}-model"
        self.script = list(script)
        self.calls: list[list[dict]] = []

    def complete(self, messages, *, json_mode=True):
        self.calls.append(messages)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return Completion(item, self.name, self.model, 5)


def ok_if_good(text):
    return (text, []) if text == "good" else (None, ["not good"])


class Usage:
    def __init__(self):
        self.rows = []

    def record(self, attempt):
        self.rows.append(attempt)


MESSAGES = [{"role": "user", "content": "hi"}]


# ------------------------------------------------------------------------ rate limiter


def test_limiter_counts_per_minute_and_day():
    clock = FakeClock()
    lim = RateLimiter(rpm=2, rpd=3, clock=clock)
    assert lim.try_acquire() and lim.try_acquire()
    assert not lim.try_acquire()  # third in the same minute
    clock.t += 61
    assert lim.try_acquire()
    clock.t += 61
    assert not lim.try_acquire()  # day budget of 3 used
    clock.t += 86400
    assert lim.try_acquire()  # a new UTC day


def test_limiter_cool_down():
    clock = FakeClock()
    lim = RateLimiter(rpm=10, rpd=10, clock=clock)
    lim.cool_down(30)
    assert lim.cooling and not lim.try_acquire()
    clock.t += 31
    assert lim.try_acquire()


# ------------------------------------------------------------------------------ router


def test_first_good_answer_wins():
    a, b = FakeProvider("a", ["good"]), FakeProvider("b", ["good"])
    res = LLMRouter([a, b]).generate(MESSAGES, ok_if_good)
    assert (res.value, res.provider) == ("good", "a")
    assert b.calls == []


def test_rate_limit_moves_on_and_cools_the_provider():
    clock = FakeClock()
    lim = RateLimiter(10, 100, clock=clock)
    a = FakeProvider("a", [RateLimited("429", retry_after=120)])
    b = FakeProvider("b", ["good"])
    res = LLMRouter([a, b], limiters={"a": lim}).generate(MESSAGES, ok_if_good)
    assert res.provider == "b"
    assert [x.outcome for x in res.attempts] == ["rate_limited", "ok"]
    clock.t += 100
    assert lim.cooling
    clock.t += 30
    assert not lim.cooling


def test_transient_errors_back_off_and_retry_once():
    sleeps = []
    a = FakeProvider("a", [ProviderError("timeout", retryable=True), "good"])
    res = LLMRouter([a], sleep=sleeps.append).generate(MESSAGES, ok_if_good)
    assert res.value == "good" and sleeps == [0.5]
    a = FakeProvider("a", [ProviderError("500", retryable=True)] * 2)
    b = FakeProvider("b", ["good"])
    sleeps.clear()
    res = LLMRouter([a, b], sleep=sleeps.append).generate(MESSAGES, ok_if_good)
    assert res.provider == "b" and sleeps == [0.5]


def test_a_rejected_key_cools_for_an_hour():
    clock = FakeClock()
    lim = RateLimiter(10, 100, clock=clock)
    a = FakeProvider("a", [AuthFailed("401", status=401)])
    LLMRouter([a], limiters={"a": lim}).generate(MESSAGES, ok_if_good)
    clock.t += 3500
    assert lim.cooling


def test_an_invalid_answer_gets_one_retry_with_the_reasons():
    a = FakeProvider("a", ["bad", "good"])
    res = LLMRouter([a]).generate(MESSAGES, ok_if_good)
    assert res.value == "good"
    retry = a.calls[1]
    assert retry[-2] == {"role": "assistant", "content": "bad"}
    assert "not good" in retry[-1]["content"]


def test_two_invalid_answers_move_to_the_next_provider_then_give_up():
    a = FakeProvider("a", ["bad", "bad"])
    b = FakeProvider("b", ["bad", "bad"])
    usage = Usage()
    res = LLMRouter([a, b], usage=usage).generate(MESSAGES, ok_if_good)
    assert res.value is None
    assert [x.outcome for x in usage.rows] == ["invalid"] * 4


def test_over_budget_providers_are_skipped():
    lim = RateLimiter(rpm=0, rpd=0)
    a, b = FakeProvider("a", ["good"]), FakeProvider("b", ["good"])
    res = LLMRouter([a, b], limiters={"a": lim}).generate(MESSAGES, ok_if_good)
    assert res.provider == "b" and a.calls == []
    assert res.attempts[0].outcome == "skipped"


def test_time_budget_stops_the_chain():
    clock = FakeClock(0)

    class Slow(FakeProvider):
        def complete(self, messages, *, json_mode=True):
            clock.t += 30
            return super().complete(messages, json_mode=json_mode)

    a, b = Slow("a", ["bad"]), FakeProvider("b", ["good"])
    res = LLMRouter([a, b], budget_seconds=25, clock=clock).generate(MESSAGES, ok_if_good)
    assert res.value is None and b.calls == []


# --------------------------------------------------------------- OpenAI-compatible client


def _provider(handler) -> OpenAICompatibleProvider:
    config = ProviderConfig("groq", "https://example.test/v1", "k", "m", 10, 10)
    return OpenAICompatibleProvider(config, httpx.Client(transport=httpx.MockTransport(handler)))


def test_client_sends_a_chat_completion_and_reads_the_reply():
    seen = {}

    def handler(req: httpx.Request):
        seen["url"], seen["auth"] = str(req.url), req.headers["authorization"]
        seen["body"] = req.read()
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    out = _provider(handler).complete(MESSAGES)
    assert out.text == "{}" and out.provider == "groq"
    assert seen["url"] == "https://example.test/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
    assert b'"response_format":{"type":"json_object"}' in seen["body"].replace(b" ", b"")


@pytest.mark.parametrize(
    ("status", "headers", "error", "retryable"),
    [
        (429, {"retry-after": "7"}, RateLimited, False),
        (401, {}, AuthFailed, False),
        (503, {}, ProviderError, True),
        (400, {}, ProviderError, False),
    ],
)
def test_client_maps_http_errors(status, headers, error, retryable):
    p = _provider(lambda req: httpx.Response(status, headers=headers, json={}))
    with pytest.raises(error) as info:
        p.complete(MESSAGES)
    assert info.value.retryable is retryable
    if status == 429:
        assert info.value.retry_after == 7


def test_client_timeout_is_retryable():
    def handler(req):
        raise httpx.ReadTimeout("slow", request=req)

    with pytest.raises(ProviderError) as info:
        _provider(handler).complete(MESSAGES)
    assert info.value.retryable


def test_limiter_budgets_tokens_per_minute():
    clock = FakeClock()
    lim = RateLimiter(rpm=30, rpd=1000, tpm=8000, clock=clock)
    assert lim.try_acquire(3000) and lim.try_acquire(3000)
    assert not lim.try_acquire(3000)  # 9,000 would pass the 8,000 a minute
    assert 0 < lim.wait_seconds() <= 60
    clock.t += 60
    assert lim.try_acquire(3000)


def test_client_reads_geminis_reset_time_from_the_body():
    body = {"error": {"details": [{"retryDelay": "60148s"}]}}
    p = _provider(lambda req: httpx.Response(429, json=[body]))
    with pytest.raises(RateLimited) as info:
        p.complete(MESSAGES)
    assert info.value.retry_after == 60148


def test_client_sends_reply_cap_and_provider_extras():
    seen = {}

    def handler(req):
        seen["body"] = req.read()
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    config = ProviderConfig(
        "groq",
        "https://example.test/v1",
        "k",
        "m",
        10,
        10,
        max_tokens=900,
        extra={"reasoning_effort": "low"},
    )
    OpenAICompatibleProvider(config, httpx.Client(transport=httpx.MockTransport(handler))).complete(
        MESSAGES
    )
    body = seen["body"].replace(b" ", b"")
    assert b'"max_tokens":900' in body and b'"reasoning_effort":"low"' in body
