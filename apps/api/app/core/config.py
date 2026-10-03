"""Settings read from environment variables (see .env.example at the repo root)."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = API_ROOT.parents[1]

# The repo-root .env (git-ignored) holds local secrets such as LLM keys. It wins over
# variables inherited from the machine (a stray GEMINI_API_KEY from another project, say).
# On a host without a .env, the host's environment is used as is. Tests skip it entirely.
if not os.getenv("VEDIC_ASTRO_IGNORE_DOTENV"):
    load_dotenv(REPO_ROOT / ".env", override=True)


def _list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str] = field(
        default_factory=lambda: _list(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
    )
    # Nominatim and Photon both ask for an identifying User-Agent, ideally with contact info.
    geocoder_user_agent: str = os.getenv("GEOCODER_USER_AGENT", "vedic-astro/0.1 (development)")
    photon_url: str = os.getenv("PHOTON_URL", "https://photon.komoot.io/api/")
    nominatim_url: str = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
    geocode_cache_path: str = os.getenv(
        "GEOCODE_CACHE_PATH", str(API_ROOT / ".cache" / "geocode.sqlite3")
    )
    geocode_cache_ttl_days: int = int(os.getenv("GEOCODE_CACHE_TTL_DAYS", "30"))
    # Stand-in for the `readings` Supabase table (Phase 7): narrated readings and LLM usage.
    readings_cache_path: str = os.getenv(
        "READINGS_CACHE_PATH", str(API_ROOT / ".cache" / "readings.sqlite3")
    )
    # Provider order (names in app/llm/providers.yaml). Unset: the default order. "none":
    # no LLM at all, rule texts only. Each needs its key; ones without a key are skipped.
    llm_providers: list[str] | None = field(
        default_factory=lambda: (
            None
            if os.getenv("LLM_PROVIDERS") is None
            else [p for p in _list(os.getenv("LLM_PROVIDERS", "")) if p != "none"]
        )
    )
    # Whole narration request, across retries and fallbacks, before rule-only text is shown.
    llm_budget_seconds: float = float(os.getenv("LLM_BUDGET_SECONDS", "25"))


settings = Settings()
