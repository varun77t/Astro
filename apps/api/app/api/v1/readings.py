from fastapi import APIRouter, Request

from app.api.errors import birth_time_http_error
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
def create_narration(area: Area, req: NarrationRequest, request: Request) -> Narration:
    """The area's reading written as prose by a model, or the rule texts when none answers."""
    narrator: Narrator = request.app.state.narrator
    try:
        return narrator.narrate(req, area, req.as_of, req.language)
    except BirthTimeError as exc:
        raise birth_time_http_error(exc) from exc
