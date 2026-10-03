"""Dasha periods for a birth, as the API returns them."""

from datetime import UTC, datetime, timedelta

from app.engine.dasha import YEAR_DAYS, Period, running_at, subdivide, vimshottari
from app.engine.ephemeris import moon_longitude
from app.engine.time_utils import resolve_birth_time
from app.schemas.birth import BirthInput
from app.schemas.dasha import CurrentDasha, DashaPeriod, DashaResponse, Mahadasha


def _period(p: Period) -> DashaPeriod:
    return DashaPeriod(lord=p.lord, start=p.start, end=p.end)


def compute_dasha_for(birth: BirthInput, as_of: datetime | None = None) -> DashaResponse:
    """All periods, the ones running at `as_of`, and how far a loose birth time moves them."""
    resolved = resolve_birth_time(
        birth.local_datetime(), birth.tz_name, birth.fold, birth.utc_offset_minutes
    )
    seq = vimshottari(moon_longitude(resolved.jd_ut), resolved.utc)

    # Redo the sequence at both ends of the birth-time window. If the Moon stays in the same
    # nakshatra the order holds and only the dates slide; otherwise the order itself is unsure.
    window = birth.window_minutes() / 1440
    edges = [
        vimshottari(moon_longitude(resolved.jd_ut + d), resolved.utc + timedelta(days=d))
        for d in (-window, window)
    ]
    reliable = all(e.first_lord == seq.first_lord for e in edges)
    uncertainty = (
        max(abs((e.epoch - seq.epoch).total_seconds()) for e in edges) / 86400 if reliable else None
    )

    now = as_of or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    current, pratyantardashas = None, []
    if md := running_at(seq.mahadashas, now):
        ad = running_at(md.children, now)
        pds = subdivide(ad.lord, ad.start, ad.end)
        current = CurrentDasha(
            mahadasha=_period(md),
            antardasha=_period(ad),
            pratyantardasha=_period(running_at(pds, now)),
        )
        pratyantardashas = [_period(p) for p in pds]

    return DashaResponse(
        year_days=YEAR_DAYS,
        moon_nakshatra=seq.nakshatra,
        first_lord=seq.first_lord,
        balance_years=seq.balance_years,
        as_of=now,
        mahadashas=[
            Mahadasha(
                lord=m.lord, start=m.start, end=m.end, antardashas=[_period(a) for a in m.children]
            )
            for m in seq.mahadashas
        ],
        current=current,
        pratyantardashas=pratyantardashas,
        timing_reliable=reliable,
        uncertainty_days=uncertainty,
    )
