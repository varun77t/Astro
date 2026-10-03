"""Turns a rule reading into a prompt. The model only narrates; it gets the matched rules and
the chart facts, and nothing that identifies the person (no name, birth date or place)."""

import hashlib
import json

from app.engine.constants import PLANETS, SIGNS
from app.interpret.facts import ChartFacts
from app.llm.base import Message
from app.schemas.reading import Reading, Statement

# Bump when the prompt or the output contract changes: it's part of the cache key.
PROMPT_VERSION = "3"

SYSTEM = """You write one section of a Vedic astrology reading for a single life area.

Use ONLY the rules and chart facts you are given. Never add a placement, sign, house, \
dignity, aspect or yoga that is not in them, and never contradict them.

Voice: frank and plain. Say what the tradition reads in the chart, hard things included, \
without softening, moralising or giving advice the rules don't give. Second person. Short \
sentences. No numbers, degrees or percentages. You may name a planet, sign or house only as \
the facts state it.

Never: predict death, an accident or an injury; name a specific illness; tell anyone to skip \
medical care; recommend a specific investment or purchase; mention remedies (gemstones, \
pujas, yantras); use words of certainty such as "definitely", "guaranteed" or "for sure".

Return one JSON object and nothing else:
{
  "summary": "2 or 3 sentences: the overall picture for this area",
  "strengths": [{"text": "1 or 2 sentences", "rule_ids": ["..."]}],
  "watch_points": [{"text": "...", "rule_ids": ["..."]}],
  "current_period_note": {"text": "...", "rule_ids": ["..."]} or null
}

Rules for the JSON:
- Every rule id in "strengths" must be cited in "strengths", every one in "watch_points" in \
"watch_points", every one in "current_period" in "current_period_note". Cite each id only in \
its own list.
- Write it fresh, as one connected reading: merge rules that point the same way into one \
point, link a reading to the placement behind it, and don't repeat any rule's wording. Never \
drop a rule, least of all a hard one.
- current_period_note is null only when no current_period rules are given.
- summary at most 350 characters; each point at most 220, plus about 100 for each extra rule \
it combines."""


def _planet_line(f: ChartFacts, name: str) -> dict:
    p = f.planets[name]
    line = {"planet": name, "sign": SIGNS[p.sign], "house": p.house}
    if f.basis == "ascendant":
        line["house_from_moon"] = p.house_from_moon
    if p.dignity:
        line["dignity"] = p.dignity
    if p.retrograde and name not in ("Rahu", "Ketu"):
        line["retrograde"] = True
    if p.combust:
        line["combust"] = True
    return line


def chart_payload(f: ChartFacts) -> dict:
    """The chart as the model sees it: signs, houses and dignities, nothing personal."""
    payload: dict = {
        "houses_counted_from": "Lagna" if f.basis == "ascendant" else "the Moon's sign",
        "lagna": SIGNS[f.lagna] if f.basis == "ascendant" and f.lagna is not None else None,
        "planets": [_planet_line(f, n) for n in PLANETS],
    }
    if f.periods:
        payload["running_periods"] = {
            ("main" if level == "maha" else "sub"): {
                "planet": p.lord,
                "until": f"{p.end:%B %Y}",
            }
            for level, p in f.periods.items()
        }
    return payload


def _rule(s: Statement) -> dict:
    return {
        "id": s.rule_id,
        "title": s.title,
        "reading": s.text,
        "because": [b.text for b in s.because],
    }


def build_payload(reading: Reading, facts: ChartFacts, language: str, rules_version: str) -> dict:
    return {
        "area": reading.title,
        "language": language,
        "chart": chart_payload(facts),
        "strengths": [_rule(s) for s in reading.strengths],
        "watch_points": [_rule(s) for s in reading.watch_points],
        "current_period": [_rule(s) for s in reading.current_period],
        "versions": {"rules": rules_version, "prompt": PROMPT_VERSION},
    }


def input_hash(payload: dict) -> str:
    """Cache key: the same facts and rules always give the same reading."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def build_messages(payload: dict) -> list[Message]:
    user = {k: v for k, v in payload.items() if k != "versions"}
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False, separators=(",", ":"))},
    ]
