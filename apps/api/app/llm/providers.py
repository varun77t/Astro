"""Builds the configured providers from providers.yaml plus the environment."""

import os
from pathlib import Path

import httpx
import yaml

from app.llm.base import ProviderConfig
from app.llm.openai_compat import OpenAICompatibleProvider

PROVIDERS_FILE = Path(__file__).resolve().parent / "providers.yaml"

# Strongest first; the lighter Gemini models are a backup with their own daily quotas.
DEFAULT_ORDER = ["gemini", "gemini_35", "groq", "gemini_lite", "gemini_lite_31"]


def load_provider_configs(order: list[str]) -> list[ProviderConfig]:
    """Configs for the named providers, in order, skipping any without an API key."""
    raw = yaml.safe_load(PROVIDERS_FILE.read_text(encoding="utf-8"))
    configs = []
    for name in order:
        if name not in raw:
            raise ValueError(f"unknown LLM provider {name!r}; known: {sorted(raw)}")
        spec = raw[name]
        key = os.getenv(spec["key_env"], "").strip()
        if not key:
            continue
        env = name.upper()
        configs.append(
            ProviderConfig(
                name=name,
                base_url=spec["base_url"],
                api_key=key,
                model=os.getenv(f"{env}_MODEL", spec["model"]),
                rpm=int(os.getenv(f"{env}_RPM", spec["rpm"])),
                rpd=int(os.getenv(f"{env}_RPD", spec["rpd"])),
                tpm=int(os.getenv(f"{env}_TPM", spec["tpm"])) if "tpm" in spec else None,
                max_tokens=int(spec.get("max_tokens", 1200)),
                extra=dict(spec.get("extra") or {}),
                json_mode=spec.get("json_mode", True),
                timeout_seconds=float(spec.get("timeout_seconds", 20)),
                headers=dict(spec.get("headers") or {}),
            )
        )
    return configs


def resolve_order(configured: list[str] | None) -> list[str]:
    return DEFAULT_ORDER if configured is None else configured


def build_providers(order: list[str]) -> list[OpenAICompatibleProvider]:
    configs = load_provider_configs(order)
    if not configs:
        return []
    # One connection pool for all of them; each request sets its own timeout.
    client = httpx.Client()
    return [OpenAICompatibleProvider(c, client) for c in configs]
