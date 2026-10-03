"""Plain-language notes about the UTC offset used, for the confirmation screen.

These target the historical cases where a recorded birth time is most often in a
different time standard than the one the timezone database assumes.
"""

from datetime import datetime, timedelta

WAR_TIME_OFFSET = timedelta(hours=6, minutes=30)


def is_india_war_time(local: datetime, tz_name: str) -> bool:
    """tzdata encodes 1941-45 War Time as DST; we report it separately."""
    return tz_name == "Asia/Kolkata" and local.utcoffset() == WAR_TIME_OFFSET


def is_daylight_saving(local: datetime, tz_name: str) -> bool:
    return bool(local.dst()) and not is_india_war_time(local, tz_name)


def abbreviation(local: datetime) -> str | None:
    """'IST', 'EDT'; None for numeric placeholders like '+0630' that tzdata uses."""
    name = local.tzname()
    return name if name and name.isalpha() else None


def offset_notes(local: datetime, tz_name: str, overridden: bool) -> list[str]:
    if overridden:
        return ["Using your custom UTC offset."]

    notes = []
    if local.tzname() == "LMT":
        notes.append("No time zone existed here yet, so local mean time is used.")
    if tz_name == "Asia/Kolkata":
        if is_india_war_time(local, tz_name):
            notes.append(
                "India's clocks ran an hour ahead during World War II, so UTC+06:30 is used."
            )
    if is_daylight_saving(local, tz_name):
        notes.append(f"Daylight saving was on ({local.tzname()}). Enter the time clocks showed.")
    return notes
