"""Every rule: it parses, stays inside the guardrails, and fires on its own test chart."""

import pytest

from app.interpret.guardrails import violations
from app.knowledge.rules import load_rules
from tests.rule_charts import chart_from_spec

RULES = [r for area in load_rules().values() for r in area.rules]


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.id)
def test_rule_fires_on_its_test_chart(rule):
    facts = chart_from_spec(rule.spec.test)
    reasons = rule.condition.eval(facts)
    assert reasons is not None, f"{rule.id} did not match {rule.spec.test}"
    assert reasons, f"{rule.id} matched but gave no reason to show"
    for b in reasons:
        assert b.text and b.text[0].isupper(), b.text


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.id)
def test_rule_text_passes_guardrails(rule):
    s = rule.spec
    assert violations(f"{s.title} {s.effect}") == []
    assert len(s.effect) <= 180, f"{s.id} effect is too long for one reading line"


def test_ids_carry_their_area():
    prefix = {
        "education": "EDU",
        "career": "CAR",
        "money": "MON",
        "health": "HEA",
        "relationships": "REL",
    }
    for area, rules in load_rules().items():
        for r in rules.rules:
            assert r.id.startswith(prefix[area] + "-"), r.id


def test_every_area_has_a_quiet_period_fallback():
    for area in load_rules().values():
        fallback = [r for r in area.rules if r.spec.when == {"period": "maha"}]
        assert len(fallback) == 1, area.area
        assert fallback[0].spec.group, "the fallback must share a group with the real period rules"


def test_rule_counts():
    counts = {a: len(r.rules) for a, r in load_rules().items()}
    assert counts["education"] >= 40 and counts["career"] >= 40, counts
    assert min(counts.values()) >= 25, counts
