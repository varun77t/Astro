"""What the router needs from an LLM provider, and the errors it understands."""

from dataclasses import dataclass, field
from typing import Protocol

Message = dict[str, str]  # {"role": "system" | "user" | "assistant", "content": "..."}


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    api_key: str
    model: str
    rpm: int
    rpd: int
    tpm: int | None = None  # tokens per minute, where that's the binding limit
    max_tokens: int = 1200  # cap on the reply (reasoning models count their thinking too)
    extra: dict = field(default_factory=dict)  # provider-specific request fields
    json_mode: bool = True
    timeout_seconds: float = 20
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Completion:
    text: str
    provider: str
    model: str
    latency_ms: int


class ProviderError(Exception):
    """A call failed. `retryable` errors (timeouts, 5xx) are worth one more try after a pause."""

    def __init__(self, message: str, *, retryable: bool = False, status: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status = status


class RateLimited(ProviderError):
    """429: the provider wants us to back off, possibly for a stated number of seconds."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message, retryable=False, status=429)
        self.retry_after = retry_after


class AuthFailed(ProviderError):
    """401/403: a bad or revoked key. Nothing will work until the key is fixed."""


class LLMProvider(Protocol):
    name: str
    model: str

    def complete(self, messages: list[Message], *, json_mode: bool = True) -> Completion: ...
