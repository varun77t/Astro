"""Tries providers in order until one returns something the validator accepts.

Per provider:
- skip it if it's over its per-minute or per-day budget, or cooling down;
- 429: cool it down (for Retry-After, else a minute) and move on;
- a rejected key: cool it down for an hour and move on;
- timeouts and 5xx: wait (exponential backoff) and try once more, then move on;
- an answer the validator rejects: ask once more with the reasons, then move on.
Everything stops when the time budget runs out; the caller then shows rule-only text.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar

from app.llm.base import AuthFailed, LLMProvider, Message, ProviderError, RateLimited
from app.llm.rate_limiter import RateLimiter

T = TypeVar("T")
Parse = Callable[[str], tuple[T | None, list[str]]]
Outcome = Literal["ok", "invalid", "rate_limited", "auth", "error", "skipped"]

RATE_LIMIT_COOLDOWN = 60.0
AUTH_COOLDOWN = 3600.0


@dataclass(frozen=True)
class Attempt:
    provider: str
    model: str
    outcome: Outcome
    latency_ms: int = 0
    detail: str = ""


@dataclass
class RouterResult(Generic[T]):
    value: T | None = None
    provider: str | None = None
    model: str | None = None
    attempts: list[Attempt] = field(default_factory=list)


class UsageSink:
    """Where each provider call is recorded. The readings cache implements this."""

    def record(self, attempt: Attempt) -> None: ...


def estimate_tokens(provider: LLMProvider, messages: list[Message]) -> int:
    """Rough cost of a call against a tokens-per-minute budget: about 4 characters per token
    in, plus the most the reply may use."""
    prompt = sum(len(m["content"]) for m in messages) // 4
    config = getattr(provider, "config", None)
    return prompt + (config.max_tokens if config else 0)


def retry_message(errors: list[str]) -> Message:
    listed = "\n".join(f"- {e}" for e in errors[:8])
    return {
        "role": "user",
        "content": "Your answer was rejected:\n"
        f"{listed}\n"
        "Fix every point and return the complete JSON object again, nothing else.",
    }


class LLMRouter:
    def __init__(
        self,
        providers: list[LLMProvider],
        *,
        limiters: dict[str, RateLimiter] | None = None,
        usage: UsageSink | None = None,
        budget_seconds: float = 25.0,
        backoff_base: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.providers = providers
        self.limiters = limiters or {}
        self.usage = usage
        self.budget_seconds = budget_seconds
        self.backoff_base = backoff_base
        self._sleep = sleep
        self._clock = clock

    @property
    def available(self) -> bool:
        return bool(self.providers)

    def _record(self, result: RouterResult, attempt: Attempt) -> None:
        result.attempts.append(attempt)
        if self.usage is not None and attempt.outcome != "skipped":
            self.usage.record(attempt)

    def _acquire(self, provider: LLMProvider, convo: list[Message]) -> bool:
        limiter = self.limiters.get(provider.name)
        return limiter is None or limiter.try_acquire(estimate_tokens(provider, convo))

    def _cool(self, provider: LLMProvider, seconds: float) -> None:
        if limiter := self.limiters.get(provider.name):
            limiter.cool_down(seconds)

    def generate(self, messages: list[Message], parse: Parse[T]) -> RouterResult[T]:
        result: RouterResult[T] = RouterResult()
        deadline = self._clock() + self.budget_seconds

        for provider in self.providers:
            convo = list(messages)
            transient_retries = validation_retries = 0
            while True:
                if self._clock() >= deadline:
                    return result
                if not self._acquire(provider, convo):
                    self._record(
                        result,
                        Attempt(
                            provider.name,
                            provider.model,
                            "skipped",
                            0,
                            "over budget or cooling down",
                        ),
                    )
                    break
                try:
                    completion = provider.complete(convo)
                except RateLimited as exc:
                    self._cool(provider, exc.retry_after or RATE_LIMIT_COOLDOWN)
                    self._record(result, Attempt(provider.name, provider.model, "rate_limited"))
                    break
                except AuthFailed as exc:
                    self._cool(provider, AUTH_COOLDOWN)
                    self._record(
                        result, Attempt(provider.name, provider.model, "auth", 0, str(exc))
                    )
                    break
                except ProviderError as exc:
                    self._record(
                        result, Attempt(provider.name, provider.model, "error", 0, str(exc))
                    )
                    if exc.retryable and transient_retries < 1:
                        self._sleep(self.backoff_base * 2**transient_retries)
                        transient_retries += 1
                        continue
                    break

                value, errors = parse(completion.text)
                if value is not None:
                    self._record(
                        result,
                        Attempt(provider.name, completion.model, "ok", completion.latency_ms),
                    )
                    result.value, result.provider = value, provider.name
                    result.model = completion.model
                    return result
                self._record(
                    result,
                    Attempt(
                        provider.name,
                        completion.model,
                        "invalid",
                        completion.latency_ms,
                        "; ".join(errors[:3]),
                    ),
                )
                if validation_retries >= 1:
                    break
                validation_retries += 1
                convo = [
                    *messages,
                    {"role": "assistant", "content": completion.text},
                    retry_message(errors),
                ]
        return result
