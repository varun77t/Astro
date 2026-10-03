from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.geo.geocoder import Geocoder, GeocoderUnavailable
from app.geo.timezones import timezone_for
from app.schemas.geo import GeocodeResponse, TimezoneResponse

router = APIRouter()


def get_geocoder(request: Request) -> Geocoder:
    return request.app.state.geocoder


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode(
    geocoder: Annotated[Geocoder, Depends(get_geocoder)],
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> GeocodeResponse:
    try:
        return GeocodeResponse(results=await geocoder.search(q, limit))
    except GeocoderUnavailable as exc:
        raise HTTPException(
            status_code=503, detail={"code": "geocoder_unavailable", "message": str(exc)}
        ) from exc


@router.get("/timezone", response_model=TimezoneResponse)
def timezone(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
) -> TimezoneResponse:
    """For places entered as raw coordinates."""
    tz_name = timezone_for(lat, lon)
    if tz_name is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "timezone_not_found", "message": "No timezone found here."},
        )
    return TimezoneResponse(tz_name=tz_name)
