"""Evaluates the YAML rules' `when` conditions against chart facts.

A condition is a small tree. Leaves look at one planet, one house, the Lagna or a pair of
house lords; `all`, `any` and `not` combine them. Every leaf that holds also says, in plain
words, which placement made it hold. Those sentences are the reading's "Why this?".

Planet leaves pick a subject with one of
    planet: Jupiter      lord_of: 5      period: maha | antar
and then test it with any of
    is  house  sign  dignity  retrograde  combust  with  not_with  with_lord_of
    aspected_by  rules  nakshatra  d9_sign  d9_dignity  vargottama  from
House leaves (`house: 5` and no planet subject) take `has`, `empty` and `aspected_by`.
Also: `lagna: [Leo, ...]` and `exchange: [9, 10]`. See docs/rule-writing-guide.md.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.engine.constants import NAKSHATRAS, PLANETS, SIGN_LORDS, SIGNS
from app.interpret.facts import ChartFacts, PlanetFacts

HOUSE_SETS = {
    "kendra": (1, 4, 7, 10),
    "trikona": (1, 5, 9),
    "dusthana": (6, 8, 12),
    "upachaya": (3, 6, 10, 11),
}
DIGNITY_SETS = {
    "strong": ("exalted", "moolatrikona", "own"),
    "weak": ("debilitated",),
}
DIGNITIES = ("exalted", "moolatrikona", "own", "friendly", "neutral", "enemy", "debilitated")
PLANET_GROUPS = ("benefic", "malefic")

DIGNITY_WORDS = {
    "exalted": "is exalted",
    "moolatrikona": "is in its own sign",
    "own": "is in its own sign",
    "friendly": "is in a friendly sign",
    "neutral": "is in a neutral sign",
    "enemy": "is in an unfriendly sign",
    "debilitated": "is debilitated",
}
D9_DIGNITY_WORDS = {
    "exalted": "is exalted in your navamsa",
    "own": "is in its own sign in your navamsa",
    "debilitated": "is debilitated in your navamsa",
}


class RuleError(ValueError):
    """A rule's `when` block doesn't parse. Raised at load time, never while matching."""


@dataclass(frozen=True)
class Because:
    text: str
    planets: tuple[str, ...] = ()
    houses: tuple[int, ...] = ()


# A matched condition returns the reasons it holds (possibly none, e.g. for `not`);
# an unmatched one returns None.
Result = list[Because] | None


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def house_words(facts: ChartFacts, house: int, from_moon: bool = False) -> str:
    if from_moon or facts.basis == "moon":
        return f"the {ordinal(house)} house from your Moon"
    return f"your {ordinal(house)} house"


def _join(parts: list[str]) -> str:
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def named(planet: str) -> str:
    """ "the Sun", "the Moon", "Jupiter"."""
    return f"the {planet}" if planet in ("Sun", "Moon") else planet


def _names(names: list[str] | tuple[str, ...]) -> str:
    return _join([named(n) for n in names])


def _sentence(text: str) -> str:
    return text[0].upper() + text[1:]


# ------------------------------------------------------------------------- value parsing


def _as_list(value: Any) -> list:
    return list(value) if isinstance(value, list | tuple) else [value]


def _houses(value: Any) -> frozenset[int]:
    out: set[int] = set()
    for v in _as_list(value):
        if isinstance(v, str) and v in HOUSE_SETS:
            out.update(HOUSE_SETS[v])
        elif isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 12:
            out.add(v)
        else:
            raise RuleError(f"not a house: {v!r}")
    return frozenset(out)


def _signs(value: Any) -> frozenset[int]:
    out = set()
    for v in _as_list(value):
        if v not in SIGNS:
            raise RuleError(f"not a sign: {v!r}")
        out.add(SIGNS.index(v))
    return frozenset(out)


def _dignities(value: Any) -> frozenset[str]:
    out: set[str] = set()
    for v in _as_list(value):
        if v in DIGNITY_SETS:
            out.update(DIGNITY_SETS[v])
        elif v in DIGNITIES:
            out.add(v)
        else:
            raise RuleError(f"not a dignity: {v!r}")
    return frozenset(out)


def _planet_refs(value: Any) -> tuple[str, ...]:
    refs = tuple(_as_list(value))
    for v in refs:
        if v not in PLANETS and v not in PLANET_GROUPS:
            raise RuleError(f"not a planet or group: {v!r}")
    return refs


def _resolve(refs: tuple[str, ...], facts: ChartFacts) -> set[str]:
    out: set[str] = set()
    for r in refs:
        if r == "benefic":
            out |= facts.benefics
        elif r == "malefic":
            out |= facts.malefics
        else:
            out.add(r)
    return out


def _bool(value: Any, key: str) -> bool:
    if not isinstance(value, bool):
        raise RuleError(f"{key} must be true or false")
    return value


# ------------------------------------------------------------------- planet predicates
#
# Each predicate tests the subject planet and returns (holds, phrase). The phrase is the
# verb part of the sentence ("is in your 5th house") or None when there's nothing to say.

Pred = Callable[[ChartFacts, PlanetFacts, bool], tuple[bool, str | None, tuple[int, ...]]]


def _pred_house(value: Any) -> Pred:
    houses = _houses(value)

    def test(f: ChartFacts, p: PlanetFacts, from_moon: bool):
        h = p.house_from_moon if from_moon else p.house
        return h in houses, f"is in {house_words(f, h, from_moon)}", (h,)

    return test


def _pred_sign(value: Any) -> Pred:
    signs = _signs(value)
    return lambda f, p, m: (p.sign in signs, f"is in {SIGNS[p.sign]}", ())


def _pred_dignity(value: Any) -> Pred:
    wanted = _dignities(value)
    return lambda f, p, m: (p.dignity in wanted, DIGNITY_WORDS.get(p.dignity or ""), ())


def _pred_flag(key: str, value: Any, word: str) -> Pred:
    want = _bool(value, key)
    return lambda f, p, m: (getattr(p, key) == want, word if want else None, ())


def _pred_with(value: Any, negate: bool) -> Pred:
    refs = _planet_refs(value)

    def test(f: ChartFacts, p: PlanetFacts, m: bool):
        others = sorted(
            (q for q in _resolve(refs, f) if q != p.name and f.planets[q].sign == p.sign),
            key=PLANETS.index,
        )
        if negate:
            return not others, None, ()
        return bool(others), f"sits with {_names(others)}" if others else None, ()

    return test


def _pred_with_lord_of(value: Any) -> Pred:
    houses = _houses(value)
    if len(houses) != 1:
        raise RuleError("with_lord_of takes a single house")
    house = next(iter(houses))

    def test(f: ChartFacts, p: PlanetFacts, m: bool):
        lord = f.lord_of(house)
        ok = lord != p.name and f.planets[lord].sign == p.sign
        return ok, f"sits with {named(lord)}, ruler of {house_words(f, house)}", (house,)

    return test


def _pred_aspected_by(value: Any) -> Pred:
    refs = _planet_refs(value)

    def test(f: ChartFacts, p: PlanetFacts, m: bool):
        by = [q for q in f.aspecting(p.sign) if q in _resolve(refs, f) and q != p.name]
        by.sort(key=PLANETS.index)
        return bool(by), f"receives the aspect of {_names(by)}" if by else None, ()

    return test


def _pred_rules(value: Any) -> Pred:
    houses = _houses(value)

    def test(f: ChartFacts, p: PlanetFacts, m: bool):
        ruled = [h for h in f.houses_ruled_by(p.name) if h in houses]
        words = _join([ordinal(h) for h in ruled]) if ruled else ""
        plural = "houses" if len(ruled) > 1 else "house"
        text = (
            f"rules the {words} {plural} from your Moon"
            if f.basis == "moon"
            else f"rules your {words} {plural}"
        )
        return bool(ruled), text if ruled else None, tuple(ruled)

    return test


def _pred_nakshatra(value: Any) -> Pred:
    wanted = set(_as_list(value))
    if not wanted <= set(NAKSHATRAS):
        raise RuleError(f"not a nakshatra: {sorted(wanted - set(NAKSHATRAS))}")

    def test(f: ChartFacts, p: PlanetFacts, m: bool):
        name = NAKSHATRAS[int(p.longitude // (360 / 27)) % 27]
        return name in wanted, f"is in {name} nakshatra", ()

    return test


def _pred_d9_sign(value: Any) -> Pred:
    signs = _signs(value)
    return lambda f, p, m: (p.d9_sign in signs, f"is in {SIGNS[p.d9_sign]} in your navamsa", ())


def _pred_d9_dignity(value: Any) -> Pred:
    wanted = _dignities(value)
    return lambda f, p, m: (p.d9_dignity in wanted, D9_DIGNITY_WORDS.get(p.d9_dignity or ""), ())


def _pred_vargottama(value: Any) -> Pred:
    want = _bool(value, "vargottama")
    word = "keeps the same sign in your navamsa" if want else None
    return lambda f, p, m: (p.vargottama == want, word, ())


def _pred_is(value: Any) -> Pred:
    refs = _planet_refs(value)
    return lambda f, p, m: (p.name in _resolve(refs, f), None, ())


PREDICATES: dict[str, Callable[[Any], Pred]] = {
    "is": _pred_is,
    "house": _pred_house,
    "sign": _pred_sign,
    "dignity": _pred_dignity,
    "retrograde": lambda v: _pred_flag("retrograde", v, "is retrograde"),
    "combust": lambda v: _pred_flag("combust", v, "is combust, close to the Sun"),
    "with": lambda v: _pred_with(v, negate=False),
    "not_with": lambda v: _pred_with(v, negate=True),
    "with_lord_of": _pred_with_lord_of,
    "aspected_by": _pred_aspected_by,
    "rules": _pred_rules,
    "nakshatra": _pred_nakshatra,
    "d9_sign": _pred_d9_sign,
    "d9_dignity": _pred_d9_dignity,
    "vargottama": _pred_vargottama,
}


# ------------------------------------------------------------------------- conditions


class Condition:
    def eval(self, facts: ChartFacts) -> Result:
        raise NotImplementedError


@dataclass(frozen=True)
class PlanetCondition(Condition):
    planet: str | None
    lord_of: int | None
    period: str | None
    from_moon: bool
    preds: tuple[Pred, ...]
    tests_house: bool

    def _subject(self, facts: ChartFacts) -> str | None:
        if self.planet:
            return self.planet
        if self.lord_of:
            return facts.lord_of(self.lord_of)
        period = facts.periods.get(self.period or "")
        return period.lord if period else None

    def eval(self, facts: ChartFacts) -> Result:
        name = self._subject(facts)
        if name is None:
            return None
        # Counting houses from the Moon puts the Moon in the 1st by definition; that says nothing.
        if name == "Moon" and self.tests_house and (facts.basis == "moon" or self.from_moon):
            return None
        p = facts.planets[name]
        phrases, houses = [], []
        for pred in self.preds:
            ok, phrase, hs = pred(facts, p, self.from_moon)
            if not ok:
                return None
            if phrase:
                phrases.append(phrase)
            houses.extend(hs)

        reasons = []
        subject = named(name)
        if self.lord_of:
            subject = f"{named(name)}, ruler of {house_words(facts, self.lord_of)},"
            houses.insert(0, self.lord_of)
        if self.period:
            period = facts.periods[self.period]
            kind = "period" if self.period == "maha" else "sub-period"
            reasons.append(
                Because(f"Your {name} {kind} runs until {period.end:%b %Y}", planets=(name,))
            )
        if self.lord_of and not phrases:
            reasons.append(
                Because(
                    _sentence(f"{named(name)} rules {house_words(facts, self.lord_of)}"),
                    (name,),
                    (self.lord_of,),
                )
            )
        if phrases:
            reasons.append(
                Because(
                    _sentence(f"{subject} {_join(phrases)}"), planets=(name,), houses=tuple(houses)
                )
            )
        return reasons


@dataclass(frozen=True)
class HouseCondition(Condition):
    house: int
    has: tuple[str, ...] | None
    empty: bool | None
    aspected_by: tuple[str, ...] | None

    def eval(self, facts: ChartFacts) -> Result:
        where = house_words(facts, self.house)
        here = sorted(facts.in_house(self.house), key=PLANETS.index)
        reasons = []
        if self.empty is not None:
            if bool(here) == self.empty:
                return None
            if self.empty:
                reasons.append(Because(f"No planets sit in {where}", houses=(self.house,)))
        if self.has is not None:
            # In a Moon-based reading the Moon always sits in the 1st, so it can't count as one.
            wanted = _resolve(self.has, facts) - ({"Moon"} if facts.basis == "moon" else set())
            found = [p for p in here if p in wanted]
            if not found:
                return None
            verb = "is" if len(found) == 1 else "are"
            reasons.append(
                Because(
                    _sentence(f"{_names(found)} {verb} in {where}"), tuple(found), (self.house,)
                )
            )
        if self.aspected_by is not None:
            sign = facts.house_sign(self.house)
            by = sorted(
                (q for q in facts.aspecting(sign) if q in _resolve(self.aspected_by, facts)),
                key=PLANETS.index,
            )
            if not by:
                return None
            verb = "aspects" if len(by) == 1 else "aspect"
            reasons.append(
                Because(_sentence(f"{_names(by)} {verb} {where}"), tuple(by), (self.house,))
            )
        return reasons


@dataclass(frozen=True)
class LagnaCondition(Condition):
    signs: frozenset[int]

    def eval(self, facts: ChartFacts) -> Result:
        if facts.basis != "ascendant" or facts.lagna not in self.signs:
            return None
        return [Because(f"Your Lagna is {SIGNS[facts.lagna]}", houses=(1,))]


@dataclass(frozen=True)
class ExchangeCondition(Condition):
    a: int
    b: int

    def eval(self, facts: ChartFacts) -> Result:
        la, lb = facts.lord_of(self.a), facts.lord_of(self.b)
        if la == lb:
            return None
        pa, pb = facts.planets[la], facts.planets[lb]
        if SIGN_LORDS[SIGNS[pa.sign]] != lb or SIGN_LORDS[SIGNS[pb.sign]] != la:
            return None
        a, b = ordinal(self.a), ordinal(self.b)
        houses = (
            f"the {a} and {b} houses from your Moon"
            if facts.basis == "moon"
            else f"your {a} and {b} houses"
        )
        text = _sentence(
            f"{named(la)} and {named(lb)}, rulers of {houses}, sit in each other's signs"
        )
        return [Because(text, (la, lb), (self.a, self.b))]


@dataclass(frozen=True)
class All(Condition):
    parts: tuple[Condition, ...]

    def eval(self, facts: ChartFacts) -> Result:
        reasons: list[Because] = []
        for c in self.parts:
            r = c.eval(facts)
            if r is None:
                return None
            reasons.extend(r)
        return reasons


@dataclass(frozen=True)
class Any_(Condition):
    parts: tuple[Condition, ...]

    def eval(self, facts: ChartFacts) -> Result:
        for c in self.parts:
            r = c.eval(facts)
            if r is not None:
                return r
        return None


@dataclass(frozen=True)
class Not(Condition):
    part: Condition

    def eval(self, facts: ChartFacts) -> Result:
        return [] if self.part.eval(facts) is None else None


# ---------------------------------------------------------------------------- parsing

SUBJECTS = ("planet", "lord_of", "period")


def parse_condition(raw: Any) -> Condition:
    if isinstance(raw, list):
        return All(tuple(parse_condition(r) for r in raw))
    if not isinstance(raw, dict) or not raw:
        raise RuleError(f"a condition must be a non-empty mapping, got {raw!r}")

    combinators = {"all", "any", "not"} & raw.keys()
    if combinators:
        if len(raw) != 1:
            raise RuleError(f"{sorted(combinators)} must stand alone in a condition")
        key, value = next(iter(raw.items()))
        if key == "not":
            return Not(parse_condition(value))
        if not isinstance(value, list) or not value:
            raise RuleError(f"{key} takes a non-empty list")
        parts = tuple(parse_condition(v) for v in value)
        return All(parts) if key == "all" else Any_(parts)

    if "lagna" in raw:
        if len(raw) != 1:
            raise RuleError("lagna must stand alone")
        return LagnaCondition(_signs(raw["lagna"]))

    if "exchange" in raw:
        pair = raw["exchange"]
        if len(raw) != 1 or not isinstance(pair, list) or len(pair) != 2:
            raise RuleError("exchange takes two houses and stands alone")
        a, b = (next(iter(_houses(h))) for h in pair)
        return ExchangeCondition(a, b)

    subjects = [k for k in SUBJECTS if k in raw]
    if len(subjects) > 1:
        raise RuleError(f"pick one subject, got {subjects}")
    if not subjects:
        return _parse_house(raw)

    rest = dict(raw)
    planet = lord_of = period = None
    match subjects[0]:
        case "planet":
            planet = rest.pop("planet")
            if planet not in PLANETS:
                raise RuleError(f"not a planet: {planet!r}")
        case "lord_of":
            houses = _houses(rest.pop("lord_of"))
            if len(houses) != 1:
                raise RuleError("lord_of takes a single house")
            lord_of = next(iter(houses))
        case "period":
            period = rest.pop("period")
            if period not in ("maha", "antar"):
                raise RuleError(f"period is maha or antar, got {period!r}")
    from_moon = False
    if "from" in rest:
        if rest.pop("from") != "moon":
            raise RuleError("from only takes 'moon'")
        from_moon = True
    unknown = set(rest) - PREDICATES.keys()
    if unknown:
        raise RuleError(f"unknown keys {sorted(unknown)}")
    if period is None and not rest:
        raise RuleError("a planet condition needs at least one test")
    if from_moon and "house" not in rest:
        raise RuleError("from: moon only changes how `house` is counted")
    return PlanetCondition(
        planet=planet,
        lord_of=lord_of,
        period=period,
        from_moon=from_moon,
        preds=tuple(PREDICATES[k](v) for k, v in rest.items()),
        tests_house="house" in rest,
    )


def _parse_house(raw: dict) -> HouseCondition:
    if "house" not in raw:
        raise RuleError(f"no subject in {raw!r}")
    unknown = set(raw) - {"house", "has", "empty", "aspected_by"}
    if unknown:
        raise RuleError(f"unknown keys for a house {sorted(unknown)}")
    houses = _houses(raw["house"])
    if len(houses) != 1:
        raise RuleError("a house condition takes a single house")
    if len(raw) == 1:
        raise RuleError("a house condition needs has, empty or aspected_by")
    return HouseCondition(
        house=next(iter(houses)),
        has=_planet_refs(raw["has"]) if "has" in raw else None,
        empty=_bool(raw["empty"], "empty") if "empty" in raw else None,
        aspected_by=_planet_refs(raw["aspected_by"]) if "aspected_by" in raw else None,
    )
