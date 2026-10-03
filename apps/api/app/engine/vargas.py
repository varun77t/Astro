"""Divisional charts (vargas)."""

from app.engine.constants import normalize

NAVAMSA_SPAN = 30.0 / 9  # 3°20'


def navamsa_sign_index(longitude: float) -> int:
    """D9 sign. Each sign is split into nine 3°20' parts, counted continuously from Aries.

    This single formula reproduces the classical rule: movable signs start their navamsas
    from themselves, fixed signs from the 9th sign, dual signs from the 5th.
    """
    return int(normalize(longitude) // NAVAMSA_SPAN) % 12
