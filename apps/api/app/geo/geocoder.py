"""Place search: Photon first (built for search-as-you-type), Nominatim as fallback.

Nominatim's usage policy forbids client-side autocomplete and allows ~1 request/second,
so it is only hit when Photon fails, behind a 1 s throttle. Every successful answer is
cached, so repeated queries never leave the server.
"""

import asyncio
import time

import httpx

from app.geo.cache import GeocodeCache
from app.geo.timezones import timezone_for
from app.schemas.geo import Place

# Photon layers that correspond to settlements rather than streets or buildings.
PHOTON_LAYERS = ["city", "district", "locality", "county"]
PHOTON_OSM_KEYS = {"place", "boundary"}


class GeocoderUnavailable(Exception):
    """Every provider failed; the user can retry or enter coordinates manually."""


class Throttle:
    def __init__(self, min_interval: float):
        self._min_interval = min_interval
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self) -> None:
        async with self._lock:
            delay = self._last + self._min_interval - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            self._last = time.monotonic()


def normalize_query(query: str) -> str:
    return " ".join(query.lower().split())


def _join(*parts: str | None) -> str:
    seen: list[str] = []
    for part in parts:
        if part and part not in seen:
            seen.append(part)
    return ", ".join(seen)


def parse_photon(data: dict) -> list[tuple[str, str, float, float, str | None]]:
    rows = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        if props.get("osm_key") not in PHOTON_OSM_KEYS or not props.get("name"):
            continue
        lon, lat = feature["geometry"]["coordinates"][:2]
        display = _join(props["name"], props.get("state"), props.get("country"))
        code = props.get("countrycode")
        rows.append(
            (props["name"], display, float(lat), float(lon), code.upper() if code else None)
        )
    return rows


def parse_nominatim(data: list) -> list[tuple[str, str, float, float, str | None]]:
    rows = []
    for item in data:
        address = item.get("address", {})
        name = item.get("name") or item["display_name"].split(",")[0]
        display = _join(name, address.get("state"), address.get("country"))
        code = address.get("country_code")
        rows.append(
            (name, display, float(item["lat"]), float(item["lon"]), code.upper() if code else None)
        )
    return rows


class Geocoder:
    def __init__(
        self,
        client: httpx.AsyncClient,
        cache: GeocodeCache,
        photon_url: str,
        nominatim_url: str,
        nominatim_interval: float = 1.0,
    ):
        self._client = client
        self._cache = cache
        self._photon_url = photon_url
        self._nominatim_url = nominatim_url
        self._nominatim_throttle = Throttle(nominatim_interval)

    async def search(self, query: str, limit: int = 5, lang: str = "en") -> list[Place]:
        key = normalize_query(query)
        cached = self._cache.get(key, lang)
        if cached is not None:
            return cached[:limit]

        try:
            rows, source = await self._photon(key, limit, lang), "photon"
        except (httpx.HTTPError, KeyError, ValueError):
            try:
                rows, source = await self._nominatim(key, limit, lang), "nominatim"
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                raise GeocoderUnavailable("Place search is temporarily unavailable.") from exc

        places = []
        for name, display, lat, lon, code in rows:
            tz_name = timezone_for(lat, lon)
            if tz_name and display not in {p.display_name for p in places}:
                places.append(
                    Place(
                        name=name,
                        display_name=display,
                        lat=lat,
                        lon=lon,
                        country_code=code,
                        tz_name=tz_name,
                        source=source,
                    )
                )
        self._cache.set(key, lang, places)
        return places[:limit]

    async def _photon(self, query: str, limit: int, lang: str) -> list:
        params = [("q", query), ("limit", str(limit + 3)), ("lang", lang)]
        params += [("layer", layer) for layer in PHOTON_LAYERS]
        response = await self._client.get(self._photon_url, params=params)
        response.raise_for_status()
        return parse_photon(response.json())

    async def _nominatim(self, query: str, limit: int, lang: str) -> list:
        await self._nominatim_throttle.wait()
        params = {
            "q": query,
            "format": "jsonv2",
            "limit": limit,
            "addressdetails": 1,
            "featureType": "settlement",
            "accept-language": lang,
        }
        response = await self._client.get(self._nominatim_url, params=params)
        response.raise_for_status()
        return parse_nominatim(response.json())
