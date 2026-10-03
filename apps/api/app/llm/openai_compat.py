"""One client for every provider here: Gemini, Groq and OpenRouter all accept OpenAI-style
chat-completion requests, so each provider is just a base URL, a key, a model and limits."""

import re
import time

import httpx

from app.llm.base import (
    AuthFailed,
    Completion,
    Message,
    ProviderConfig,
    ProviderError,
    RateLimited,
)


def _retry_after(res: httpx.Response) -> float | None:
    """Seconds until the provider will take requests again, from the header or the body.

    Gemini sends no header but puts it in the body ("retryDelay": "60148s"), which matters:
    its free quota is daily, so retrying every minute would only burn attempts.
    """
    value = res.headers.get("retry-after")
    try:
        if value:
            return float(value)
    except ValueError:
        pass
    if m := re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', res.text):
        return float(m.group(1))
    return None


class OpenAICompatibleProvider:
    def __init__(self, config: ProviderConfig, client: httpx.Client | None = None):
        self.config = config
        self.name = config.name
        self.model = config.model
        self._client = client or httpx.Client(timeout=config.timeout_seconds)

    def complete(self, messages: list[Message], *, json_mode: bool = True) -> Completion:
        body: dict = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": self.config.max_tokens,
            **self.config.extra,
        }
        if json_mode and self.config.json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.config.api_key}", **self.config.headers}

        started = time.perf_counter()
        try:
            res = self._client.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",
                json=body,
                headers=headers,
                timeout=self.config.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ProviderError(f"{self.name}: timed out", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name}: {type(exc).__name__}", retryable=True) from exc
        latency = int((time.perf_counter() - started) * 1000)

        if res.status_code == 429:
            raise RateLimited(f"{self.name}: rate limited", _retry_after(res))
        if res.status_code in (401, 403):
            raise AuthFailed(f"{self.name}: key rejected", status=res.status_code)
        if res.status_code >= 500:
            raise ProviderError(
                f"{self.name}: server error", retryable=True, status=res.status_code
            )
        if res.status_code >= 400:
            raise ProviderError(f"{self.name}: request rejected", status=res.status_code)

        try:
            text = res.json()["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name}: unexpected response shape", retryable=True) from exc
        return Completion(text=text, provider=self.name, model=self.model, latency_ms=latency)
