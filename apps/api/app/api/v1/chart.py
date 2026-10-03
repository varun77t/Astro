from fastapi import APIRouter

from app.api.errors import birth_time_http_error
from app.engine.chart import compute_chart_for
from app.engine.time_utils import BirthTimeError
from app.schemas.birth import BirthInput
from app.schemas.chart import Chart

router = APIRouter()


@router.post("/chart", response_model=Chart)
def create_chart(birth: BirthInput) -> Chart:
    try:
        return compute_chart_for(birth)
    except BirthTimeError as exc:
        raise birth_time_http_error(exc) from exc
