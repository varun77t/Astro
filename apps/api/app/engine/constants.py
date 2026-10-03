"""Fixed astrological reference data. See docs/calculation-conventions.md."""

ENGINE_VERSION = "0.1.0"

# Locked conventions (v1). Changing any of these changes chart output, so bump ENGINE_VERSION.
AYANAMSA = "lahiri"
HOUSE_SYSTEM = "whole_sign"
NODE_TYPE = "mean"
EPHEMERIS = "moshier"  # Swiss Ephemeris built-in analytic ephemeris, no data files needed

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

# Vimshottari order; nakshatra i is ruled by NAKSHATRA_LORD_CYCLE[i % 9].
NAKSHATRA_LORD_CYCLE = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

NAKSHATRA_SPAN = 360.0 / 27  # 13°20'
PADA_SPAN = NAKSHATRA_SPAN / 4  # 3°20'

EXALTATION_SIGN = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mars": "Capricorn",
    "Mercury": "Virgo",
    "Jupiter": "Cancer",
    "Venus": "Pisces",
    "Saturn": "Libra",
    # Nodes are disputed in the classics; this is the most common modern convention.
    "Rahu": "Taurus",
    "Ketu": "Scorpio",
}

DEBILITATION_SIGN = {
    planet: SIGNS[(SIGNS.index(sign) + 6) % 12] for planet, sign in EXALTATION_SIGN.items()
}

OWN_SIGNS = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

# (sign, start_deg, end_deg) within the sign, per Brihat Parashara Hora Shastra.
MOOLATRIKONA = {
    "Sun": ("Leo", 0, 20),
    "Moon": ("Taurus", 3, 30),
    "Mars": ("Aries", 0, 12),
    "Mercury": ("Virgo", 15, 20),
    "Jupiter": ("Sagittarius", 0, 10),
    "Venus": ("Libra", 0, 15),
    "Saturn": ("Aquarius", 0, 20),
}

# Naisargika (natural) relationships. Anything not listed as friend or enemy is neutral.
NATURAL_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
NATURAL_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

# Combustion orbs in degrees from the Sun: (direct, retrograde).
COMBUSTION_ORB = {
    "Moon": (12, 12),
    "Mars": (17, 17),
    "Mercury": (14, 12),
    "Jupiter": (11, 11),
    "Venus": (10, 8),
    "Saturn": (15, 15),
}


def sign_index(longitude: float) -> int:
    return int(normalize(longitude) // 30) % 12


def normalize(longitude: float) -> float:
    lon = longitude % 360.0
    return 0.0 if lon >= 360.0 else lon
