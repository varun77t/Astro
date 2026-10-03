from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import birth, chart, dasha, geocode, glossary, readings
from app.core.config import settings
from app.engine.constants import ENGINE_VERSION
from app.geo.cache import GeocodeCache
from app.geo.geocoder import Geocoder
from app.interpret.narration_service import Narrator
from app.llm.cache import ReadingCache
from app.llm.providers import build_providers, resolve_order
from app.llm.rate_limiter import RateLimiter
from app.llm.router import LLMRouter


def build_narrator() -> Narrator:
    cache = ReadingCache(settings.readings_cache_path)
    providers = build_providers(resolve_order(settings.llm_providers))
    router = LLMRouter(
        providers,
        limiters={p.name: RateLimiter(p.config.rpm, p.config.rpd, p.config.tpm) for p in providers},
        usage=cache,
        budget_seconds=settings.llm_budget_seconds,
    )
    return Narrator(router, cache)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(
        headers={"User-Agent": settings.geocoder_user_agent}, timeout=8.0
    ) as client:
        app.state.geocoder = Geocoder(
            client,
            GeocodeCache(settings.geocode_cache_path, settings.geocode_cache_ttl_days),
            settings.photon_url,
            settings.nominatim_url,
        )
        app.state.narrator = build_narrator()
        yield


app = FastAPI(title="Vedic Astro API", version=ENGINE_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(chart.router, prefix="/api/v1", tags=["chart"])
app.include_router(birth.router, prefix="/api/v1", tags=["birth"])
app.include_router(geocode.router, prefix="/api/v1", tags=["geocode"])
app.include_router(glossary.router, prefix="/api/v1", tags=["glossary"])
app.include_router(dasha.router, prefix="/api/v1", tags=["dasha"])
app.include_router(readings.router, prefix="/api/v1", tags=["readings"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine_version": ENGINE_VERSION}
