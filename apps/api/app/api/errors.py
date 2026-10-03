from fastapi import HTTPException

from app.engine.time_utils import AmbiguousLocalTime, BirthTimeError


def birth_time_http_error(exc: BirthTimeError) -> HTTPException:
    """422 with a machine-readable code; ambiguous times carry both UTC choices."""
    if isinstance(exc, AmbiguousLocalTime):
        return HTTPException(
            status_code=422,
            detail={
                "code": "ambiguous_local_time",
                "message": str(exc),
                "options_utc": [o.isoformat() for o in exc.options],
            },
        )
    return HTTPException(
        status_code=422, detail={"code": "invalid_birth_time", "message": str(exc)}
    )
