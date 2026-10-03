import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.geocode import get_geocoder
from app.geo.cache import GeocodeCache
from app.geo.geocoder import Geocoder, GeocoderUnavailable, normalize_query
from app.main import app

PHOTON_MYSORE = {
    "features": [
        {
            "geometry": {"coordinates": [76.6553609, 12.3051828]},
            "properties": {
                "name": "Mysuru",
                "state": "Karnataka",
                "country": "India",
                "countrycode": "IN",
                "osm_key": "place",
                "osm_value": "city",
            },
        },
        {
            "geometry": {"coordinates": [76.6988633, 12.3031299]},
            "properties": {
                "name": "Mysore Mega Dairy",
                "state": "Karnataka",
                "country": "India",
                "countrycode": "IN",
                "osm_key": "landuse",
                "osm_value": "industrial",
            },
        },
    ]
}
NOMINATIM_MYSORE = [
    {
        "lat": "12.3051828",
        "lon": "76.6553609",
        "name": "Mysuru",
        "display_name": "Mysuru, Mysuru taluk, Karnataka, 570001, India",
        "address": {"state": "Karnataka", "country": "India", "country_code": "in"},
    },
]


class FakeProviders:
    def __init__(self, photon_status=200, nominatim_status=200):
        self.photon_status = photon_status
        self.nominatim_status = nominatim_status
        self.calls: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        self.calls.append(host)
        if host == "photon.test":
            return httpx.Response(self.photon_status, json=PHOTON_MYSORE)
        return httpx.Response(self.nominatim_status, json=NOMINATIM_MYSORE)


def make_geocoder(providers: FakeProviders) -> Geocoder:
    client = httpx.AsyncClient(transport=httpx.MockTransport(providers))
    return Geocoder(
        client,
        GeocodeCache(":memory:"),
        "https://photon.test/api/",
        "https://nominatim.test/search",
        nominatim_interval=0,
    )


async def _search(geocoder: Geocoder, q: str):
    return await geocoder.search(q)


@pytest.fixture
def run():
    import asyncio

    return lambda coro: asyncio.run(coro)


def test_photon_results_get_timezones_and_skip_non_places(run):
    providers = FakeProviders()
    places = run(make_geocoder(providers).search("mysore"))
    assert [p.display_name for p in places] == ["Mysuru, Karnataka, India"]
    assert places[0].tz_name == "Asia/Kolkata"
    assert places[0].country_code == "IN"
    assert places[0].source == "photon"
    assert providers.calls == ["photon.test"]


def test_falls_back_to_nominatim(run):
    providers = FakeProviders(photon_status=502)
    places = run(make_geocoder(providers).search("mysore"))
    assert places[0].source == "nominatim"
    assert places[0].display_name == "Mysuru, Karnataka, India"
    assert providers.calls == ["photon.test", "nominatim.test"]


def test_all_providers_down(run):
    with pytest.raises(GeocoderUnavailable):
        run(make_geocoder(FakeProviders(503, 503)).search("mysore"))


def test_cache_prevents_repeat_requests(run):
    providers = FakeProviders()
    geocoder = make_geocoder(providers)

    async def twice():
        await geocoder.search("Mysore")
        return await geocoder.search("  mysore ")

    assert run(twice())[0].name == "Mysuru"
    assert providers.calls == ["photon.test"]


def test_normalize_query():
    assert normalize_query("  New   DELHI ") == "new delhi"


def test_geocode_endpoint():
    app.dependency_overrides[get_geocoder] = lambda: make_geocoder(FakeProviders())
    try:
        client = TestClient(app)
        res = client.get("/api/v1/geocode", params={"q": "mysore"})
        assert res.status_code == 200
        assert res.json()["results"][0]["tz_name"] == "Asia/Kolkata"
        assert client.get("/api/v1/geocode", params={"q": "m"}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_geocode_endpoint_unavailable():
    app.dependency_overrides[get_geocoder] = lambda: make_geocoder(FakeProviders(500, 500))
    try:
        res = TestClient(app).get("/api/v1/geocode", params={"q": "mysore"})
        assert res.status_code == 503
        assert res.json()["detail"]["code"] == "geocoder_unavailable"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("lat", "lon", "tz"),
    [
        (12.97, 77.59, "Asia/Kolkata"),
        (-33.87, 151.21, "Australia/Sydney"),
        (27.7, 85.3, "Asia/Kathmandu"),
        (40.71, -74.0, "America/New_York"),
    ],
)
def test_timezone_endpoint(lat, lon, tz):
    res = TestClient(app).get("/api/v1/timezone", params={"lat": lat, "lon": lon})
    assert res.json() == {"tz_name": tz}
