"""Assembles the full chart JSON from the individual engine modules."""

from datetime import datetime

from app.engine import ephemeris
from app.engine.constants import (
    AYANAMSA,
    ENGINE_VERSION,
    EPHEMERIS,
    HOUSE_SYSTEM,
    NODE_TYPE,
    SIGN_LORDS,
    SIGNS,
    sign_index,
)
from app.engine.houses import house_lord, house_sign, whole_sign_house
from app.engine.nakshatra import nakshatra_of
from app.engine.reliability import assess_reliability
from app.engine.strength import dignity, is_combust
from app.engine.time_utils import resolve_birth_time
from app.engine.vargas import navamsa_sign_index
from app.schemas.birth import EXACT_WINDOW_MINUTES, BirthInput, TimeAccuracy
from app.schemas.chart import (
    AscendantPosition,
    Chart,
    ChartMeta,
    DivisionalChart,
    DivisionalPlacement,
    House,
    PlanetPosition,
)


def format_offset(dt: datetime) -> str:
    total_minutes = int(dt.utcoffset().total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def compute_chart_for(birth: BirthInput) -> Chart:
    return compute_chart(
        birth.local_datetime(),
        birth.tz_name,
        birth.lat,
        birth.lon,
        birth.fold,
        utc_offset_minutes=birth.utc_offset_minutes,
        time_accuracy=birth.time_accuracy,
        window_minutes=birth.window_minutes(),
    )


def compute_chart(
    local: datetime,
    tz_name: str,
    lat: float,
    lon: float,
    fold: int | None = None,
    *,
    utc_offset_minutes: int | None = None,
    time_accuracy: TimeAccuracy = "exact",
    window_minutes: int = EXACT_WINDOW_MINUTES,
) -> Chart:
    resolved = resolve_birth_time(local, tz_name, fold, utc_offset_minutes)
    jd = resolved.jd_ut

    asc_lon = ephemeris.ascendant_longitude(jd, lat, lon)
    asc_idx = sign_index(asc_lon)
    asc_nak = nakshatra_of(asc_lon)
    ascendant = AscendantPosition(
        longitude=asc_lon,
        sign=SIGNS[asc_idx],
        sign_lord=SIGN_LORDS[SIGNS[asc_idx]],
        degree_in_sign=asc_lon % 30,
        nakshatra=asc_nak.name,
        nakshatra_lord=asc_nak.lord,
        pada=asc_nak.pada,
    )

    bodies = ephemeris.body_positions(jd)
    sun_lon = next(b.longitude for b in bodies if b.name == "Sun")
    moon_idx = sign_index(next(b.longitude for b in bodies if b.name == "Moon"))
    planets = []
    for body in bodies:
        idx = sign_index(body.longitude)
        nak = nakshatra_of(body.longitude)
        planets.append(
            PlanetPosition(
                name=body.name,
                longitude=body.longitude,
                latitude=body.latitude,
                speed=body.speed,
                sign=SIGNS[idx],
                sign_lord=SIGN_LORDS[SIGNS[idx]],
                degree_in_sign=body.longitude % 30,
                house=whole_sign_house(idx, asc_idx),
                house_from_moon=whole_sign_house(idx, moon_idx),
                nakshatra=nak.name,
                nakshatra_lord=nak.lord,
                pada=nak.pada,
                retrograde=body.retrograde,
                combust=is_combust(body.name, body.longitude, sun_lon, body.retrograde),
                dignity=dignity(body.name, body.longitude),
            )
        )

    house_of = {p.name: p.house for p in planets}
    houses = [
        House(
            house=h,
            sign=house_sign(h, asc_idx),
            lord=house_lord(h, asc_idx),
            lord_house=house_of[house_lord(h, asc_idx)],
            occupants=[p.name for p in planets if p.house == h],
        )
        for h in range(1, 13)
    ]

    d9_asc_idx = navamsa_sign_index(asc_lon)
    d9 = DivisionalChart(
        ascendant_sign=SIGNS[d9_asc_idx],
        planets=[
            DivisionalPlacement(
                name=b.name,
                sign=SIGNS[navamsa_sign_index(b.longitude)],
                house=whole_sign_house(navamsa_sign_index(b.longitude), d9_asc_idx),
            )
            for b in bodies
        ],
    )

    meta = ChartMeta(
        ayanamsa=AYANAMSA,
        ayanamsa_value=ephemeris.ayanamsa(jd),
        house_system=HOUSE_SYSTEM,
        node_type=NODE_TYPE,
        ephemeris=EPHEMERIS,
        engine_version=ENGINE_VERSION,
        utc=resolved.utc,
        local_time=resolved.local,
        tz_name=tz_name,
        utc_offset=format_offset(resolved.local),
        offset_overridden=utc_offset_minutes is not None,
        jd_ut=jd,
    )
    reliability = assess_reliability(jd, lat, lon, window_minutes, time_accuracy)
    return Chart(
        meta=meta,
        reliability=reliability,
        ascendant=ascendant,
        planets=planets,
        houses=houses,
        divisional={"D9": d9},
    )
