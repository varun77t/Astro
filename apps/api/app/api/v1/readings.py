from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.errors import birth_time_http_error
from app.core.auth import Caller, caller
from app.core.config import settings
from app.engine.time_utils import BirthTimeError
from app.interpret.narration_service import Narrator
from app.interpret.reading_service import compute_readings_for
from app.schemas.narration import Narration, NarrationRequest
from app.schemas.reading import Area, Reading, ReadingRequest, ReadingsResponse

router = APIRouter()


@router.post("/readings", response_model=ReadingsResponse)
def create_readings(req: ReadingRequest) -> ReadingsResponse:
    """All five life areas in one go: the chart and samples are computed once."""
    try:
        return compute_readings_for(req, req.as_of)
    except BirthTimeError as exc:
        raise birth_time_http_error(exc) from exc


@router.post("/readings/{area}", response_model=Reading)
def create_reading(area: Area, req: ReadingRequest) -> Reading:
    try:
        return compute_readings_for(req, req.as_of, areas=(area,)).readings[0]
    except BirthTimeError as exc:
        raise birth_time_http_error(exc) from exc


@router.post("/readings/{area}/narration", response_model=Narration)
def create_narration(
    area: Area, req: NarrationRequest, request: Request, who: Annotated[Caller, Depends(caller)]
) -> Narration:
    """The area's reading written as prose by a model, or the rule texts when none answers.

    Each caller gets a daily allowance of fresh AI readings (more when signed in); cached
    readings don't count, and past the allowance the rule texts are returned instead.
    """
    narrator: Narrator = request.app.state.narrator
    quota = request.app.state.narration_quota
    limit = (
        settings.narrations_per_day_user if who.user_id else settings.narrations_per_day_anonymous
    )
    try:
        out = narrator.narrate(
            req, area, req.as_of, req.language, allow_llm=quota.remaining(who.key, limit) > 0
        )
    except BirthTimeError as exc:
        raise birth_time_http_error(exc) from exc
    if out.mode == "llm" and not out.cached:
        quota.spend(who.key)
    return out
