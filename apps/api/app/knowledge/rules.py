"""Loads the rule base: one YAML file per life area in knowledge/rules/.

Every rule is validated and its `when` block parsed at load time, so a typo fails at
startup (and in the tests) rather than silently never matching.
"""

import hashlib
from dataclasses import dataclass
from functools import cache
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from app.interpret.rule_matcher import Condition, PlanetCondition, parse_condition
from app.knowledge.loader import KNOWLEDGE_DIR
from app.schemas.reading import AREAS, Area, Tone

RULES_DIR = KNOWLEDGE_DIR / "rules"

Balance = Literal["supportive", "mixed", "cautionary", "quiet"]


class RuleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Z]{3}-[A-Z0-9]+(-[A-Z0-9]+)*$")
    title: str
    when: Any
    effect: str
    tone: Tone
    weight: float = Field(gt=0, le=1)
    source: str
    group: str | None = None  # of several matching rules in a group, only the strongest is shown
    needs: Literal["lagna"] | None = None  # skip when houses are counted from the Moon
    test: dict[str, Any]  # a minimal chart that should trigger the rule (see the tests)


class AreaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area: Area
    title: str
    summary: dict[Balance, str]
    disclaimer: str | None = None
    rules: list[RuleSpec]


@dataclass(frozen=True)
class Rule:
    spec: RuleSpec
    area: Area
    condition: Condition
    period: str | None  # "maha" or "antar" when the rule reads the running dasha

    @property
    def id(self) -> str:
        return self.spec.id

    @property
    def uses_period(self) -> bool:
        return self.period is not None


@dataclass(frozen=True)
class AreaRules:
    area: Area
    title: str
    summary: dict[str, str]
    disclaimer: str | None
    rules: tuple[Rule, ...]


def _period_level(c: Condition) -> str | None:
    if isinstance(c, PlanetCondition):
        return c.period
    parts = getattr(c, "parts", None) or ([c.part] if hasattr(c, "part") else [])
    return next((lvl for p in parts if (lvl := _period_level(p))), None)


def _load_area(area: Area) -> AreaRules:
    raw = yaml.safe_load((RULES_DIR / f"{area}.yaml").read_text(encoding="utf-8"))
    spec = AreaSpec.model_validate(raw)
    if spec.area != area:
        raise ValueError(f"{area}.yaml says area {spec.area}")
    if set(spec.summary) != {"supportive", "mixed", "cautionary", "quiet"}:
        raise ValueError(f"{area}.yaml needs all four summary lines")
    rules = []
    for r in spec.rules:
        try:
            cond = parse_condition(r.when)
        except ValueError as exc:
            raise ValueError(f"{r.id}: {exc}") from exc
        rules.append(Rule(spec=r, area=area, condition=cond, period=_period_level(cond)))
    return AreaRules(area, spec.title, spec.summary, spec.disclaimer, tuple(rules))


@cache
def load_rules() -> dict[Area, AreaRules]:
    areas = {a: _load_area(a) for a in AREAS}
    ids = [r.id for a in areas.values() for r in a.rules]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate rule ids: {sorted(dupes)}")
    return areas


@cache
def rules_version() -> str:
    """Changes whenever any rule file changes; part of the reading cache key later."""
    h = hashlib.sha256()
    for area in AREAS:
        h.update((RULES_DIR / f"{area}.yaml").read_bytes())
    return h.hexdigest()[:12]
