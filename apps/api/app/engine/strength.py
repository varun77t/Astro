"""Planetary dignity and combustion."""

from app.engine.constants import (
    COMBUSTION_ORB,
    DEBILITATION_SIGN,
    EXALTATION_SIGN,
    MOOLATRIKONA,
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    OWN_SIGNS,
    SIGN_LORDS,
    SIGNS,
    sign_index,
)


def dignity(planet: str, longitude: float) -> str | None:
    """One of exalted, debilitated, moolatrikona, own, friendly, neutral, enemy.

    Exaltation/debilitation are judged by sign and take precedence (so Moon anywhere in
    Taurus is "exalted"). Rahu/Ketu only get exalted/debilitated, otherwise None.
    """
    sign = SIGNS[sign_index(longitude)]
    if EXALTATION_SIGN.get(planet) == sign:
        return "exalted"
    if DEBILITATION_SIGN.get(planet) == sign:
        return "debilitated"
    if planet not in OWN_SIGNS:
        return None

    mt_sign, start, end = MOOLATRIKONA[planet]
    if sign == mt_sign and start <= longitude % 30 < end:
        return "moolatrikona"
    if sign in OWN_SIGNS[planet]:
        return "own"

    lord = SIGN_LORDS[sign]
    if lord in NATURAL_FRIENDS[planet]:
        return "friendly"
    if lord in NATURAL_ENEMIES[planet]:
        return "enemy"
    return "neutral"


def angular_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def is_combust(planet: str, longitude: float, sun_longitude: float, retrograde: bool) -> bool:
    if planet not in COMBUSTION_ORB:
        return False
    direct_orb, retro_orb = COMBUSTION_ORB[planet]
    orb = retro_orb if retrograde else direct_orb
    return angular_distance(longitude, sun_longitude) < orb
