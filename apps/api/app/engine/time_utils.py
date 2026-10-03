"""Local civil time at a place -> UTC -> Julian day (UT).

A wrong UTC offset silently moves the ascendant by ~1 sign per 2 hours, so this module
refuses to guess: times that fall in a DST gap are rejected, and times that occur twice
(DST fall-back) require the caller to pick which one via `fold`.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe


class BirthTimeError(ValueError):
    """Base class for local-time conversion problems shown to the user."""


class UnknownTimezone(BirthTimeError):
    pass


class NonexistentLocalTime(BirthTimeError):
    """The clock skipped this time (e.g. spring-forward DST gap)."""


class AmbiguousLocalTime(BirthTimeError):
    """The clock showed this time twice (e.g. fall-back DST); caller must pass fold=0 or 1."""

    def __init__(self, message: str, options: list[datetime]):
        super().__init__(message)
        self.options = options  # UTC datetimes for fold=0 and fold=1


@dataclass(frozen=True)
class ResolvedTime:
    local: datetime  # aware, in the birth timezone
    utc: datetime  # aware, UTC
    jd_ut: float


def get_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise UnknownTimezone(f"Unknown timezone: {tz_name!r}") from exc


def local_to_utc(local: datetime, tz_name: str, fold: int | None = None) -> datetime:
    """Convert a naive local wall-clock time in `tz_name` to an aware UTC datetime."""
    if local.tzinfo is not None:
        raise ValueError("local must be a naive datetime (wall-clock time at the birth place)")
    zone = get_zone(tz_name)

    first = local.replace(tzinfo=zone, fold=0)
    second = local.replace(tzinfo=zone, fold=1)

    # A wall time inside a DST gap does not survive a round trip through UTC.
    round_trip = first.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
    if round_trip != local:
        raise NonexistentLocalTime(
            f"{local:%Y-%m-%d %H:%M} did not exist in {tz_name} (clocks were moved forward). "
            "Please double-check the birth time."
        )

    if first.utcoffset() != second.utcoffset():
        options = [first.astimezone(UTC), second.astimezone(UTC)]
        if fold is None:
            raise AmbiguousLocalTime(
                f"{local:%Y-%m-%d %H:%M} occurred twice in {tz_name} (clocks were moved back). "
                "Please choose which occurrence (fold=0 for the first, fold=1 for the second).",
                options,
            )
        return options[fold]

    return first.astimezone(UTC)


def julian_day_ut(utc: datetime) -> float:
    if utc.tzinfo is None or utc.utcoffset() != timedelta(0):
        raise ValueError("utc must be an aware datetime in UTC")
    hour = utc.hour + utc.minute / 60 + (utc.second + utc.microsecond / 1e6) / 3600
    return swe.julday(utc.year, utc.month, utc.day, hour, swe.GREG_CAL)


def resolve_birth_time(
    local: datetime,
    tz_name: str,
    fold: int | None = None,
    utc_offset_minutes: int | None = None,
) -> ResolvedTime:
    """`utc_offset_minutes` overrides the IANA zone, for records kept in a local standard
    that the database doesn't model (e.g. Bombay Time, UTC+04:51, before 1955)."""
    if utc_offset_minutes is not None:
        get_zone(tz_name)  # still validate the zone name
        fixed = timezone(timedelta(minutes=utc_offset_minutes))
        aware = local.replace(tzinfo=fixed)
        utc = aware.astimezone(UTC)
        return ResolvedTime(local=aware, utc=utc, jd_ut=julian_day_ut(utc))
    utc = local_to_utc(local, tz_name, fold)
    return ResolvedTime(local=utc.astimezone(get_zone(tz_name)), utc=utc, jd_ut=julian_day_ut(utc))
