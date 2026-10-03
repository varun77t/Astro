"""A wrong UTC offset silently ruins the ascendant, so these are tested hardest."""

from datetime import UTC, datetime, timedelta

import pytest

from app.engine.time_utils import (
    AmbiguousLocalTime,
    NonexistentLocalTime,
    UnknownTimezone,
    julian_day_ut,
    local_to_utc,
)


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


@pytest.mark.parametrize(
    ("local", "tz", "expected_utc"),
    [
        # Modern IST is +05:30.
        (datetime(1990, 5, 17, 14, 35), "Asia/Kolkata", utc(1990, 5, 17, 9, 5)),
        # India wartime time (+06:30): 1941-10-01..1942-05-15 and 1942-09-01..1945-10-15.
        (datetime(1941, 9, 30, 12, 0), "Asia/Kolkata", utc(1941, 9, 30, 6, 30)),
        (datetime(1941, 10, 2, 12, 0), "Asia/Kolkata", utc(1941, 10, 2, 5, 30)),
        (datetime(1942, 6, 15, 12, 0), "Asia/Kolkata", utc(1942, 6, 15, 6, 30)),
        (datetime(1943, 6, 1, 12, 0), "Asia/Kolkata", utc(1943, 6, 1, 5, 30)),
        (datetime(1945, 10, 20, 12, 0), "Asia/Kolkata", utc(1945, 10, 20, 6, 30)),
        # Nepal moved from +05:30 to +05:45 in 1986.
        (datetime(1985, 6, 1, 12, 0), "Asia/Kathmandu", utc(1985, 6, 1, 6, 30)),
        (datetime(1990, 6, 1, 12, 0), "Asia/Kathmandu", utc(1990, 6, 1, 6, 15)),
        # UK stayed on +01:00 all year from 1968 to 1971 (British Standard Time).
        (datetime(1970, 1, 15, 12, 0), "Europe/London", utc(1970, 1, 15, 11, 0)),
        (datetime(1975, 1, 15, 12, 0), "Europe/London", utc(1975, 1, 15, 12, 0)),
        # Southern hemisphere: Sydney DST is in January, not July.
        (datetime(2024, 1, 15, 10, 0), "Australia/Sydney", utc(2024, 1, 14, 23, 0)),
        (datetime(2024, 7, 15, 10, 0), "Australia/Sydney", utc(2024, 7, 15, 0, 0)),
        # US summer time.
        (datetime(2021, 7, 4, 12, 0), "America/New_York", utc(2021, 7, 4, 16, 0)),
        # Near-midnight births cross the UTC date line.
        (datetime(2000, 1, 1, 0, 15), "Asia/Kolkata", utc(1999, 12, 31, 18, 45)),
        (datetime(1999, 12, 31, 23, 59), "Asia/Kolkata", utc(1999, 12, 31, 18, 29)),
        (datetime(2000, 1, 1, 23, 30), "America/Los_Angeles", utc(2000, 1, 2, 7, 30)),
    ],
)
def test_local_to_utc(local, tz, expected_utc):
    assert local_to_utc(local, tz) == expected_utc


def test_dst_gap_is_rejected():
    # US clocks jumped 02:00 -> 03:00 on 2021-03-14.
    with pytest.raises(NonexistentLocalTime):
        local_to_utc(datetime(2021, 3, 14, 2, 30), "America/New_York")


def test_dst_overlap_requires_a_choice():
    # US clocks went 02:00 -> 01:00 on 2021-11-07, so 01:30 happened twice.
    local = datetime(2021, 11, 7, 1, 30)
    with pytest.raises(AmbiguousLocalTime) as info:
        local_to_utc(local, "America/New_York")
    assert info.value.options == [utc(2021, 11, 7, 5, 30), utc(2021, 11, 7, 6, 30)]
    assert local_to_utc(local, "America/New_York", fold=0) == utc(2021, 11, 7, 5, 30)
    assert local_to_utc(local, "America/New_York", fold=1) == utc(2021, 11, 7, 6, 30)


def test_fold_is_ignored_when_time_is_unambiguous():
    local = datetime(1990, 5, 17, 14, 35)
    assert local_to_utc(local, "Asia/Kolkata", fold=1) == local_to_utc(local, "Asia/Kolkata")


def test_unknown_timezone():
    with pytest.raises(UnknownTimezone):
        local_to_utc(datetime(2000, 1, 1), "Mars/Olympus_Mons")


def test_rejects_aware_input():
    with pytest.raises(ValueError):
        local_to_utc(datetime(2000, 1, 1, tzinfo=UTC), "Asia/Kolkata")


def test_julian_day_epochs():
    assert julian_day_ut(utc(2000, 1, 1, 12, 0)) == pytest.approx(2451545.0, abs=1e-9)
    assert julian_day_ut(utc(1970, 1, 1, 0, 0)) == pytest.approx(2440587.5, abs=1e-9)


def test_julian_day_resolution_is_sub_second():
    base = utc(1990, 5, 17, 9, 5)
    one_second = julian_day_ut(base + timedelta(seconds=1)) - julian_day_ut(base)
    assert one_second == pytest.approx(1 / 86400, rel=1e-4)
