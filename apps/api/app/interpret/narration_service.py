"""A reading in prose: the matched rules, narrated by a model when one is available.

cache hit  -> the stored narration
cache miss -> router (providers in order, each answer validated) -> store and return
nothing valid in time, or no providers -> the rule texts as they are ("rules" mode)
"""

from datetime import datetime

from app.interpret.prompt_builder import build_messages, build_payload, input_hash
from app.interpret.reading_service import compute_readings_with_facts
from app.interpret.validator import validate
from app.llm.cache import ReadingCache
from app.llm.router import LLMRouter
from app.schemas.birth import BirthInput
from app.schemas.narration import Language, LLMReading, NarratedPoint, Narration
from app.schemas.reading import Area, Reading, Statement


def _points(statements: list[Statement]) -> list[NarratedPoint]:
    return [NarratedPoint(text=s.text, rule_ids=[s.rule_id]) for s in statements]


def rules_narration(reading: Reading, language: Language, rules_version: str) -> Narration:
    """The fallback that always works: each matched rule's own text, one per line."""
    return Narration(
        area=reading.area,
        language=language,
        mode="rules",
        provider=None,
        model=None,
        cached=False,
        summary=reading.summary,
        strengths=_points(reading.strengths),
        watch_points=_points(reading.watch_points),
        current_period=_points(reading.current_period),
        reading=reading,
        rules_version=rules_version,
    )


def _llm_narration(
    out: LLMReading,
    reading: Reading,
    language: Language,
    rules_version: str,
    *,
    provider: str,
    model: str,
    cached: bool,
) -> Narration:
    return Narration(
        area=reading.area,
        language=language,
        mode="llm",
        provider=provider,
        model=model,
        cached=cached,
        summary=out.summary,
        strengths=out.strengths,
        watch_points=out.watch_points,
        current_period=[out.current_period_note] if out.current_period_note else [],
        reading=reading,
        rules_version=rules_version,
    )


class Narrator:
    def __init__(self, router: LLMRouter | None, cache: ReadingCache | None):
        self.router = router
        self.cache = cache

    def narrate(
        self,
        birth: BirthInput,
        area: Area,
        as_of: datetime | None = None,
        language: Language = "en",
        *,
        allow_llm: bool = True,
    ) -> Narration:
        """`allow_llm=False` still serves a cached narration but never calls a provider."""
        readings, facts = compute_readings_with_facts(birth, as_of, areas=(area,))
        reading = readings.readings[0]
        version = readings.rules_version
        if not (reading.strengths or reading.watch_points or reading.current_period):
            return rules_narration(reading, language, version)  # nothing to narrate

        payload = build_payload(reading, facts, language, version)
        key = input_hash(payload)
        if self.cache and (hit := self.cache.get(key)):
            content, provider, model = hit
            out = LLMReading.model_validate(content)
            return _llm_narration(
                out, reading, language, version, provider=provider, model=model, cached=True
            )

        if not allow_llm:
            return rules_narration(reading, language, version).model_copy(
                update={"limit_reached": True}
            )
        if self.router is None or not self.router.available:
            return rules_narration(reading, language, version)
        result = self.router.generate(
            build_messages(payload), lambda text: validate(text, reading, facts)
        )
        if result.value is None:
            return rules_narration(reading, language, version)

        if self.cache:
            self.cache.set(
                key,
                area=area,
                language=language,
                rules_version=version,
                content=result.value.model_dump(),
                provider=result.provider or "",
                model=result.model or "",
            )
        return _llm_narration(
            result.value,
            reading,
            language,
            version,
            provider=result.provider or "",
            model=result.model or "",
            cached=False,
        )
