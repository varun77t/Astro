"""Checks a model's reading before anyone sees it.

Rejects when the JSON is malformed, when a point cites a rule it wasn't given (or in the
wrong list), when a given rule is left out, when the text crosses a guardrail, or when it
states a placement the chart doesn't have: a planet in the wrong house or sign, the wrong
ruler of a house, a wrong dignity, a wrong Lagna, or a yoga no rule named. The checks
look for explicit claims only, so a correct reading isn't rejected for its phrasing.
"""

import json
import re

from pydantic import ValidationError

from app.engine.constants import PLANETS, SIGNS
from app.interpret.facts import ChartFacts
from app.interpret.guardrails import violations
from app.schemas.narration import LLMReading, NarratedPoint
from app.schemas.reading import Reading

MAX_SUMMARY = 400
MAX_POINT = 260

_P = "|".join(PLANETS)
_S = "|".join(SIGNS)
ORDINAL_WORDS = [
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
    "eleventh",
    "twelfth",
]
_ORD = rf"(\d{{1,2}}(?=st|nd|rd|th)|{'|'.join(ORDINAL_WORDS)})(?:st|nd|rd|th)?"
# An optional appositive between a planet and its verb: "Venus, ruler of your 5th house, is…"
_APPOS = r"(?:,[^,.;:]{1,60},)?"

PLACED_IN_HOUSE = re.compile(
    rf"\b({_P})\b{_APPOS}\s+(?:is |sits |sitting |placed |lies )?in (?:your |the )?{_ORD} house"
    r"(\s+(?:counted )?from (?:your|the) Moon)?",
    re.IGNORECASE,
)
RULES_HOUSE = re.compile(
    rf"\b({_P})\b,?\s+(?:(?:the |which is the |as )?(?:ruler|lord) of|rules|ruling) "
    rf"(?:your |the )?{_ORD}",
    re.IGNORECASE,
)
IN_SIGN = re.compile(
    rf"\b({_P})\b{_APPOS}\s+(?:is |sits |placed )?(?:(?:exalted|debilitated) )?in ({_S})\b",
    re.IGNORECASE,
)
DIGNITY = re.compile(
    rf"\b({_P})\b{_APPOS}\s+(?:is |sits )?(exalted|debilitated|in its own sign)", re.IGNORECASE
)
LAGNA = re.compile(
    rf"\b(?:Lagna|ascendant|rising sign)\b(?:\s+sign)?(?:\s+is|,|:)?\s+(?:in\s+)?({_S})\b"
    rf"|\b({_S})\s+(?:Lagna|ascendant|rising)\b",
    re.IGNORECASE,
)
HOUSE_SIGN = re.compile(
    rf"\b{_ORD} house(\s+from your Moon)?(?:,|\s+is|\s+falls in|\s+in)?\s+({_S})\b",
    re.IGNORECASE,
)
YOGA = re.compile(r"\b([A-Z][a-z]+(?:[- ][A-Z][a-z]+)?) yoga\b")
NOT_YOGA_NAMES = {"this", "that", "the", "a", "an", "your", "such", "another", "each", "one"}


def _house_number(token: str) -> int:
    """ "7" or "seventh" -> 7."""
    return int(token) if token.isdigit() else ORDINAL_WORDS.index(token.lower()) + 1


def _point_limit(point: NarratedPoint) -> int:
    """Longer when a point combines several rules: merging is what makes prose read well."""
    return MAX_POINT + 120 * (len(point.rule_ids) - 1)


def _canon(name: str) -> str:
    return name[0].upper() + name[1:].lower()


def parse_json(text: str) -> dict | None:
    """The first JSON object in the reply, tolerating code fences and stray prose."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


# Models like typographic hyphens and quotes ("Dharma‑Karma", "don’t"); the checks don't.
_PLAIN = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "‘": "'", "’": "'", " ": " "})


def fact_errors(text: str, facts: ChartFacts, known_yogas: set[str]) -> list[str]:
    """Placements the text states that the chart doesn't have."""
    text = text.translate(_PLAIN)
    errors = []
    for m in PLACED_IN_HOUSE.finditer(text):
        p = facts.planets[_canon(m.group(1))]
        house = _house_number(m.group(2))
        from_moon = bool(m.group(3)) or facts.basis == "moon"
        actual = p.house_from_moon if from_moon else p.house
        if house != actual:
            errors.append(f"says {p.name} is in the {house} house; it is in the {actual}")
    for m in RULES_HOUSE.finditer(text):
        name, house = _canon(m.group(1)), _house_number(m.group(2))
        if 1 <= house <= 12 and facts.lord_of(house) != name:
            errors.append(f"says {name} rules house {house}; {facts.lord_of(house)} does")
    for m in IN_SIGN.finditer(text):
        p, sign = facts.planets[_canon(m.group(1))], _canon(m.group(2))
        if SIGNS[p.sign] != sign:
            errors.append(f"says {p.name} is in {sign}; it is in {SIGNS[p.sign]}")
    for m in DIGNITY.finditer(text):
        p, claim = facts.planets[_canon(m.group(1))], m.group(2).lower()
        ok = {
            "exalted": p.dignity == "exalted",
            "debilitated": p.dignity == "debilitated",
            "in its own sign": p.dignity in ("own", "moolatrikona"),
        }[claim]
        if not ok:
            errors.append(f"says {p.name} is {claim}; it is {p.dignity or 'neither'}")
    for m in LAGNA.finditer(text):
        sign = _canon(m.group(1) or m.group(2))
        if facts.basis != "ascendant" or facts.lagna is None:
            errors.append("names a Lagna sign, but the birth time can't fix the Lagna")
        elif SIGNS[facts.lagna] != sign:
            errors.append(f"says the Lagna is {sign}; it is {SIGNS[facts.lagna]}")
    for m in HOUSE_SIGN.finditer(text):
        house, sign = _house_number(m.group(1)), _canon(m.group(3))
        if not 1 <= house <= 12:
            continue
        first = facts.first_house
        if m.group(2) and facts.basis == "ascendant":
            first = facts.planets["Moon"].sign
        actual = SIGNS[(first + house - 1) % 12]
        if actual != sign:
            errors.append(f"says the {house} house is {sign}; it is {actual}")
    for m in YOGA.finditer(text):
        name = m.group(1).lower().replace("-", " ")
        if name.split()[0] in NOT_YOGA_NAMES:
            continue
        if name not in known_yogas:
            errors.append(f"names {m.group(1)} yoga, which none of the rules gives")
    if "°" in text or "%" in text:
        errors.append("uses degrees or percentages")
    return errors


def _known_yogas(reading: Reading) -> set[str]:
    words = " ".join(
        f"{s.title} {s.text}"
        for s in reading.strengths + reading.watch_points + reading.current_period
    )
    return {m.group(1).lower().replace("-", " ") for m in YOGA.finditer(words)}


def _check_points(
    label: str, points: list[NarratedPoint], given: list[str], errors: list[str]
) -> None:
    allowed = set(given)
    cited: set[str] = set()
    for i, point in enumerate(points):
        for rid in point.rule_ids:
            if rid not in allowed:
                errors.append(f"{label}[{i}] cites {rid}, which isn't one of the {label} rules")
        cited |= set(point.rule_ids)
        if len(point.text) > _point_limit(point):
            errors.append(f"{label}[{i}] is longer than {_point_limit(point)} characters")
    missing = [rid for rid in given if rid not in cited]
    if missing:
        errors.append(f"{label} leaves out {', '.join(missing)}; every rule must be covered")
    if len(points) > len(given):
        errors.append(f"{label} has more points than rules")


def validate(text: str, reading: Reading, facts: ChartFacts) -> tuple[LLMReading | None, list[str]]:
    raw = parse_json(text)
    if raw is None:
        return None, ["the reply is not a JSON object"]
    try:
        out = LLMReading.model_validate(raw)
    except ValidationError as exc:
        issues = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()[:4])
        return None, [f"the JSON doesn't match the schema ({issues})"]

    errors: list[str] = []
    _check_points("strengths", out.strengths, [s.rule_id for s in reading.strengths], errors)
    _check_points(
        "watch_points", out.watch_points, [s.rule_id for s in reading.watch_points], errors
    )
    period = [out.current_period_note] if out.current_period_note else []
    _check_points("current_period", period, [s.rule_id for s in reading.current_period], errors)
    if len(out.summary) > MAX_SUMMARY:
        errors.append(f"summary is longer than {MAX_SUMMARY} characters")

    yogas = _known_yogas(reading)
    texts = {"summary": out.summary}
    for label, points in (
        ("strengths", out.strengths),
        ("watch_points", out.watch_points),
        ("current_period", period),
    ):
        texts |= {f"{label}[{i}]": p.text for i, p in enumerate(points)}
    for where, t in texts.items():
        errors += [f"{where} {v}" for v in violations(t)]
        errors += [f"{where} {e}" for e in fact_errors(t, facts, yogas)]
    return (None, errors) if errors else (out, [])
