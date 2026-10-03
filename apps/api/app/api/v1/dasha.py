from fastapi import APIRouter

from app.api.errors import birth_time_http_error
from app.engine.dasha_report import compute_dasha_for
from app.engine.time_utils import BirthTimeError
from app.schemas.dasha import DashaRequest, DashaResponse

router = APIRouter()


@router.post("/dasha", response_model=DashaResponse)
def create_dasha(req: DashaRequest) -> DashaResponse:
    try:
        return compute_dasha_for(req, req.as_of)
    except BirthTimeError as exc:
        raise birth_time_http_error(exc) from exc
