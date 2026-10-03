"""Rule-based readings: chart facts in, matched rules out, arranged as a short reading.

A rule is shown when it holds at the given birth time. It is "sure" when it also holds at
every sample across the birth-time window, and "possible" when a different birth time inside
the window would undo it. Period rules are only sure when the running dasha can't change
within the dates' own uncertainty.
"""

from datetime import UTC, datetime, timedelta

from app.engine.chart import compute_chart_for
from app.engine.dasha_report import compute_dasha_for
from app.interpret.facts import ChartFacts, PeriodFacts, facts_at
from app.interpret.guardrails import NOTE
from app.knowledge.rules import AreaRules, Rule, load_rules, rules_version
from app.schemas.birth import BirthInput
from app.schemas.dasha import DashaPeriod, DashaResponse
from app.schemas.reading import (
    AREAS,
    Area,
    Because,
    Reading,
    ReadingsResponse,
    Statement,
)

SAMPLE_STEP_MINUTES = 10
MAX_STRENGTHS = 6
MAX_WATCH_POINTS = 4
MAX_PERIOD_NOTES = 2
# Below this total weight, an area gets the "nothing stands out" summary rather than a verdict.
QUIET_BELOW = 1.2


def sample_offsets(window_minutes: int) -> list[float]:
    """Minutes either side of the given time to re-test rules at, always including both edges."""
    step = min(SAMPLE_STEP_MINUTES, window_minutes)
    offsets = {float(m) for m in range(-window_minutes, window_minutes + 1, step)}
    offsets |= {-float(window_minutes), float(window_minutes)}
    offsets.discard(0.0)
    return sorted(offsets)


def _periods(dasha: DashaResponse) -> dict[str, PeriodFacts]:
    if dasha.current is None:
        return {}
    return {
        "maha": PeriodFacts(dasha.current.mahadasha.lord, dasha.current.mahadasha.end),
        "antar": PeriodFacts(dasha.current.antardasha.lord, dasha.current.antardasha.end),
    }


def _period_settled(dasha: DashaResponse) -> dict[str, bool]:
    """Per level: False when birth-time uncertainty could put us in a different period now."""
    if dasha.current is None or not dasha.timing_reliable or dasha.uncertainty_days is None:
        return {"maha": False, "antar": False}
    slack = timedelta(days=dasha.uncertainty_days)
    now = dasha.as_of

    def settled(p: DashaPeriod) -> bool:
        return now - p.start > slack and p.end - now > slack

    return {"maha": settled(dasha.current.mahadasha), "antar": settled(dasha.current.antardasha)}


def _statement(rule: Rule, reasons, sure: bool) -> Statement:
    return Statement(
        rule_id=rule.id,
        title=rule.spec.title,
        text=rule.spec.effect.strip(),
        tone=rule.spec.tone,
        weight=rule.spec.weight,
        certainty="sure" if sure else "possible",
        because=[
            Because(text=b.text, planets=list(b.planets), houses=list(b.houses)) for b in reasons
        ],
        source=rule.spec.source,
    )


def _rank(s: Statement) -> tuple:
    return (s.certainty != "sure", -s.weight)


def _strongest_per_group(pairs: list[tuple[Rule, Statement]]) -> list[Statement]:
    best: dict[str, Statement] = {}
    for rule, s in pairs:
        key = rule.spec.group or rule.id
        if key not in best or _rank(s) < _rank(best[key]):
            best[key] = s
    # Two rules resting on exactly the same placement would say it twice; keep the stronger.
    shown, seen = [], set()
    for s in sorted(best.values(), key=_rank):
        reasons = tuple(b.text for b in s.because)
        if reasons not in seen:
            seen.add(reasons)
            shown.append(s)
    return shown


def _balance(statements: list[Statement]) -> str:
    def total(tone: str) -> float:
        return sum(
            s.weight * (1 if s.certainty == "sure" else 0.5) for s in statements if s.tone == tone
        )

    good, hard = total("supportive"), total("cautionary")
    if good + hard < QUIET_BELOW:
        return "quiet"
    if good >= 2 * hard:
        return "supportive"
    if hard >= 2 * good:
        return "cautionary"
    return "mixed"


def read_area(
    area: AreaRules,
    center: ChartFacts,
    samples: list[ChartFacts],
    period_settled: dict[str, bool],
) -> Reading:
    matched: list[tuple[Rule, Statement]] = []
    for rule in area.rules:
        if rule.spec.needs == "lagna" and center.basis != "ascendant":
            continue
        reasons = rule.condition.eval(center)
        if reasons is None:
            continue
        sure = all(rule.condition.eval(s) is not None for s in samples)
        if rule.period:
            sure = sure and period_settled[rule.period]
        matched.append((rule, _statement(rule, reasons, sure)))

    natal = [(r, s) for r, s in matched if not r.uses_period]
    period = [(r, s) for r, s in matched if r.uses_period]
    shown = _strongest_per_group(natal)
    # Main-period notes before sub-period ones; within each, strongest first.
    level = {r.id: r.period for r, _ in period}
    period_notes = sorted(
        _strongest_per_group(period), key=lambda s: (level[s.rule_id] != "maha", *_rank(s))
    )
    # "Your period isn't tied to this area" only earns its place when nothing else is said.
    fallback = {r.id for r, _ in period if r.spec.when == {"period": "maha"}}
    if len(period_notes) > 1:
        period_notes = [s for s in period_notes if s.rule_id not in fallback]

    return Reading(
        area=area.area,
        title=area.title,
        basis=center.basis,
        summary=area.summary[_balance(shown)],
        strengths=[s for s in shown if s.tone != "cautionary"][:MAX_STRENGTHS],
        watch_points=[s for s in shown if s.tone == "cautionary"][:MAX_WATCH_POINTS],
        current_period=period_notes[:MAX_PERIOD_NOTES],
        disclaimer=area.disclaimer,
        matched_rule_ids=[r.id for r, _ in matched],
    )


def compute_readings_for(
    birth: BirthInput, as_of: datetime | None = None, areas: tuple[Area, ...] = AREAS
) -> ReadingsResponse:
    return compute_readings_with_facts(birth, as_of, areas)[0]


def compute_readings_with_facts(
    birth: BirthInput, as_of: datetime | None = None, areas: tuple[Area, ...] = AREAS
) -> tuple[ReadingsResponse, ChartFacts]:
    """The readings plus the chart facts at the given time, which narration checks against."""
    chart = compute_chart_for(birth)
    dasha = compute_dasha_for(birth, as_of or datetime.now(UTC))
    basis = chart.reliability.basis
    periods = _periods(dasha)
    jd = chart.meta.jd_ut

    center = facts_at(jd, birth.lat, birth.lon, basis, periods)
    samples = [
        facts_at(jd + m / 1440, birth.lat, birth.lon, basis, periods)
        for m in sample_offsets(birth.window_minutes())
    ]
    settled = _period_settled(dasha)
    rules = load_rules()
    response = ReadingsResponse(
        rules_version=rules_version(),
        as_of=dasha.as_of,
        note=NOTE,
        readings=[read_area(rules[a], center, samples, settled) for a in areas],
    )
    return response, center
