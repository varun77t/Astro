"""Live eval: narrate 20 charts through the real providers and check every answer.

Needs API keys in the repo-root .env. Bypasses the cache, so it spends real quota: 20 charts
x 2 areas is about 40 calls (more when answers are retried).

    python -m app.llm.eval                          # all configured providers, in order
    python -m app.llm.eval --provider groq          # one provider only
    python -m app.llm.eval --areas money --charts 5

Passing means the answer came from a model and the validator accepted it, i.e. it cites only
rules it was given, covers all of them, and contradicts no chart fact.
"""

import argparse
import json
import sys
import time
from datetime import UTC, date, datetime
from datetime import time as clock
from pathlib import Path

from app.core.config import settings
from app.interpret.prompt_builder import build_messages, build_payload
from app.interpret.reading_service import compute_readings_with_facts
from app.interpret.validator import validate
from app.llm.providers import build_providers, resolve_order
from app.llm.rate_limiter import RateLimiter
from app.llm.router import LLMRouter
from app.schemas.birth import BirthInput

GOLDEN_DIR = Path(__file__).resolve().parents[4] / "data" / "golden_charts"
AS_OF = datetime(2026, 10, 3, tzinfo=UTC)

# Eleven more births to make twenty, spread over Lagnas, latitudes and decades.
EXTRA = [
    ("hyderabad", "1996-02-11", "04:20", "Asia/Kolkata", 17.385, 78.4867),
    ("jaipur", "2001-09-23", "18:05", "Asia/Kolkata", 26.9124, 75.7873),
    ("lucknow", "1988-12-02", "10:40", "Asia/Kolkata", 26.8467, 80.9462),
    ("kochi", "2004-07-15", "21:30", "Asia/Kolkata", 9.9312, 76.2673),
    ("ahmedabad", "1999-04-04", "06:55", "Asia/Kolkata", 23.0225, 72.5714),
    ("patna", "1993-11-19", "13:15", "Asia/Kolkata", 25.5941, 85.1376),
    ("guwahati", "2007-01-28", "02:10", "Asia/Kolkata", 26.1445, 91.7362),
    ("dubai", "1998-08-08", "08:08", "Asia/Dubai", 25.2048, 55.2708),
    ("singapore", "2003-05-30", "16:45", "Asia/Singapore", 1.3521, 103.8198),
    ("toronto", "1991-10-12", "23:20", "America/Toronto", 43.6532, -79.3832),
    ("belagavi", "2010-03-03", "12:00", "Asia/Kolkata", 15.8497, 74.4977),
]


def births(limit: int) -> list[tuple[str, BirthInput]]:
    out = []
    for path in sorted(GOLDEN_DIR.glob("[!_]*.json")):
        b = json.loads(path.read_text(encoding="utf-8"))["birth"]
        out.append(
            (
                path.stem,
                BirthInput(
                    date=date.fromisoformat(b["date"]),
                    time=clock.fromisoformat(b["time"]),
                    tz_name=b["tz_name"],
                    lat=b["lat"],
                    lon=b["lon"],
                ),
            )
        )
    for city, d, t, tz, lat, lon in EXTRA:
        out.append(
            (
                f"{city}-{d[:4]}",
                BirthInput(
                    date=date.fromisoformat(d),
                    time=clock.fromisoformat(t),
                    tz_name=tz,
                    lat=lat,
                    lon=lon,
                ),
            )
        )
    return out[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--provider", help="only this provider (a name in providers.yaml)")
    ap.add_argument("--areas", default="education,career")
    ap.add_argument("--charts", type=int, default=20)
    ap.add_argument("--show", type=int, default=1, help="print this many narrations in full")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # model text may use typographic characters

    order = [args.provider] if args.provider else resolve_order(settings.llm_providers)
    providers = build_providers(order)
    if not providers:
        print("No providers configured: add GEMINI_API_KEY or GROQ_API_KEY to the repo-root .env.")
        return 2
    limiters = {p.name: RateLimiter(p.config.rpm, p.config.rpd, p.config.tpm) for p in providers}
    router = LLMRouter(providers, limiters=limiters, budget_seconds=60)

    valid = answered = no_capacity = shown = 0
    by_provider: dict[str, int] = {}
    for name, birth in births(args.charts):
        for area in args.areas.split(","):
            # Free tiers refill per minute; wait for one rather than record a non-answer.
            wait = min(lim.wait_seconds() for lim in limiters.values())
            if 0 < wait <= 90 and all(lim.wait_seconds() > 0 for lim in limiters.values()):
                time.sleep(wait + 1)
            readings, facts = compute_readings_with_facts(birth, AS_OF, areas=(area,))
            reading = readings.readings[0]
            payload = build_payload(reading, facts, "en", readings.rules_version)
            started = time.perf_counter()
            res = router.generate(
                build_messages(payload), lambda t, r=reading, f=facts: validate(t, r, f)
            )
            secs = time.perf_counter() - started
            trail = " > ".join(f"{a.provider}:{a.outcome}" for a in res.attempts)
            got_answer = any(a.outcome in ("ok", "invalid") for a in res.attempts)
            answered += got_answer
            if res.value is not None:
                valid += 1
                by_provider[res.provider] = by_provider.get(res.provider, 0) + 1
                print(f"PASS {name:<16} {area:<14} {secs:5.1f}s  {trail}")
                if shown < args.show:
                    shown += 1
                    print(json.dumps(res.value.model_dump(), indent=2, ensure_ascii=False))
            elif got_answer:
                why = next((a.detail for a in reversed(res.attempts) if a.detail), "")
                print(f"FAIL {name:<16} {area:<14} {secs:5.1f}s  {trail}  {why}")
            else:
                no_capacity += 1
                print(f"SKIP {name:<16} {area:<14} {secs:5.1f}s  {trail}  (no quota left)")

    print(
        f"\n{valid}/{answered} answers passed the validator; by provider: {by_provider}; "
        f"{no_capacity} not tried for lack of quota"
    )
    return 0 if answered and valid / answered >= 0.9 else 1


if __name__ == "__main__":
    sys.exit(main())
