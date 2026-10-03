"""Whole-sign houses: the ascendant's sign is house 1, the next sign house 2, and so on."""

from app.engine.constants import SIGN_LORDS, SIGNS


def whole_sign_house(body_sign_index: int, ascendant_sign_index: int) -> int:
    return (body_sign_index - ascendant_sign_index) % 12 + 1


def house_sign(house: int, ascendant_sign_index: int) -> str:
    return SIGNS[(ascendant_sign_index + house - 1) % 12]


def house_lord(house: int, ascendant_sign_index: int) -> str:
    return SIGN_LORDS[house_sign(house, ascendant_sign_index)]
