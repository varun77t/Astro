from fastapi import APIRouter

from app.api.errors import birth_time_http_error
from app.engine.chart import format_offset
from app.engine.time_notes import abbreviation, is_daylight_saving, offset_notes
from app.engine.time_utils import BirthTimeError, resolve_birth_time
from app.schemas.birth import BirthInput, BirthResolution

router = APIRouter()


@router.post("/birth/resolve", response_model=BirthResolution)
def resolve_birth(birth: BirthInput) -> BirthResolution:
    """Show the user exactly which UTC moment their input maps to, before charting."""
    try:
        resolved = resolve_birth_time(
            birth.local_datetime(), birth.tz_name, birth.fold, birth.utc_offset_minutes
        )
    except BirthTimeError as exc:
        raise birth_time_http_error(exc) from exc

    overridden = birth.utc_offset_minutes is not None
    return BirthResolution(
        local_time=resolved.local,
        utc=resolved.utc,
        utc_offset=format_offset(resolved.local),
        tz_name=birth.tz_name,
        tz_abbreviation=None if overridden else abbreviation(resolved.local),
        is_dst=not overridden and is_daylight_saving(resolved.local, birth.tz_name),
        offset_overridden=overridden,
        time_accuracy=birth.time_accuracy,
        time_assumed=birth.time_accuracy == "unknown",
        window_minutes=birth.window_minutes(),
        notes=offset_notes(resolved.local, birth.tz_name, overridden),
    )
