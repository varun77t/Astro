"""How much of the chart survives uncertainty in the birth time.

Samples the ascendant and Moon across the time window. The ascendant changes sign
roughly every 2 hours and the Moon every ~2.5 days, so when the time is unknown or
loose, readings fall back to the Moon sign (Rashi) instead of houses from the ascendant.
"""

from app.engine.constants import SIGNS, sign_index
from app.engine.ephemeris import ascendant_longitude, moon_longitude
from app.engine.nakshatra import nakshatra_of
from app.engine.vargas import navamsa_sign_index
from app.schemas.chart import ChartReliability

SAMPLE_STEP_MINUTES = 5


def _ordered_unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def assess_reliability(
    jd_ut: float, lat: float, lon: float, window_minutes: int, time_accuracy: str
) -> ChartReliability:
    steps = max(1, window_minutes // SAMPLE_STEP_MINUTES)
    offsets = [window_minutes * i / steps for i in range(-steps, steps + 1)]
    times = [jd_ut + minutes / 1440 for minutes in offsets]

    asc_lons = [ascendant_longitude(t, lat, lon) for t in times]
    asc_signs = _ordered_unique([SIGNS[sign_index(a)] for a in asc_lons])
    moon_lons = [moon_longitude(t) for t in times]
    moon_signs = _ordered_unique([SIGNS[sign_index(m)] for m in moon_lons])
    moon_naks = _ordered_unique([nakshatra_of(m).name for m in moon_lons])
    # The navamsa ascendant changes every ~13 minutes, so even an exact time can straddle two.
    d9_asc_signs = _ordered_unique([SIGNS[navamsa_sign_index(a)] for a in asc_lons])
    d9_moon_signs = _ordered_unique([SIGNS[navamsa_sign_index(m)] for m in moon_lons])

    ascendant_reliable = time_accuracy != "unknown" and len(asc_signs) == 1
    warnings = []
    if time_accuracy == "unknown":
        warnings.append("No birth time, so houses are counted from your Moon sign.")
    elif not ascendant_reliable:
        options = " or ".join(asc_signs)
        if time_accuracy == "exact":
            warnings.append(
                f"Your Lagna is near a sign boundary: {window_minutes} minutes either way "
                f"would make it {options}."
            )
        else:
            warnings.append(
                f"Within ±{window_minutes} minutes your Lagna could be {options}, so houses are "
                "counted from your Moon sign."
            )
    if len(moon_signs) > 1:
        warnings.append(
            f"The Moon changed sign around your birth time ({' to '.join(moon_signs)})."
        )
    if len(moon_naks) > 1:
        warnings.append(
            "The Moon changed nakshatra around your birth time, so dasha dates are approximate."
        )

    return ChartReliability(
        time_accuracy=time_accuracy,
        window_minutes=window_minutes,
        ascendant_signs=asc_signs,
        moon_signs=moon_signs,
        moon_nakshatras=moon_naks,
        ascendant_reliable=ascendant_reliable,
        moon_sign_reliable=len(moon_signs) == 1,
        moon_nakshatra_reliable=len(moon_naks) == 1,
        navamsa_ascendant_signs=d9_asc_signs,
        navamsa_moon_signs=d9_moon_signs,
        navamsa_ascendant_reliable=time_accuracy != "unknown" and len(d9_asc_signs) == 1,
        navamsa_moon_reliable=len(d9_moon_signs) == 1,
        basis="ascendant" if ascendant_reliable or time_accuracy == "exact" else "moon",
        warnings=warnings,
    )
