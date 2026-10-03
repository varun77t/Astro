# Calculation conventions

These are locked for v1. Changing any of them changes chart output for every user,
so a change must bump `ENGINE_VERSION` in `apps/api/app/engine/constants.py` (which
also invalidates cached readings keyed by chart hash).

| Topic | Convention | Where |
|---|---|---|
| Zodiac | Sidereal | `ephemeris.py` |
| Ayanamsa | **Lahiri** (`SIDM_LAHIRI`), ≈ 23°51′ at J2000. The reported `ayanamsa_value` is exactly what was subtracted (no separate nutation term). | `ephemeris.ayanamsa` |
| Ephemeris | Swiss Ephemeris **Moshier** analytic mode (`FLG_MOSEPH`); no `.se1` data files. Error is well under 1″ for planets in modern dates, far inside the 1′ golden-chart tolerance. | `ephemeris.py` |
| Python binding | `pysweph` (community fork of `pyswisseph`, same C library 2.10.03, prebuilt wheels for Windows/Linux/macOS). Imported as `swisseph`. | `pyproject.toml` |
| Lunar nodes | **Mean** node. Ketu = Rahu + 180°. Both are always reported retrograde. | `constants.NODE_TYPE` |
| House system | **Whole sign**: ascendant's sign = house 1. | `houses.py` |
| Ascendant | Swiss Ephemeris `houses_ex` with sidereal flag. | `ephemeris.ascendant_longitude` |
| Planets | Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu. No outer planets. | `constants.PLANETS` |
| Retrograde | Longitude speed < 0. | `ephemeris.BodyPosition` |
| Nakshatras | 27 × 13°20′ from 0° sidereal Aries, 4 padas of 3°20′. Lords follow Vimshottari order starting with Ketu for Ashwini. | `nakshatra.py` |
| Navamsa (D9) | 108 × 3°20′ parts counted continuously from Aries (equivalent to the movable/fixed/dual rule). | `vargas.py` |
| Dignity | Exalted / debilitated by **sign** (take precedence, so Moon anywhere in Taurus is exalted). Then moolatrikona (degree ranges per BPHS), own sign, then the sign lord's **natural** (naisargika) relationship → friendly / neutral / enemy. Temporary (tatkalika) friendship is not used yet. | `strength.py` |
| Node dignity | Rahu exalted in Taurus / debilitated in Scorpio; Ketu the reverse. Otherwise no dignity (`null`). Classical sources disagree; this is the most common modern choice. | `constants.EXALTATION_SIGN` |
| Combustion | Within these degrees of the Sun: Moon 12, Mars 17, Mercury 14 (12 if retrograde), Jupiter 11, Venus 10 (8 if retrograde), Saturn 15. Nodes never combust. | `constants.COMBUSTION_ORB` |
| Dasha (Phase 4) | Vimshottari, 120 years, year = **365.25 days**, starting from the Moon's nakshatra. | not built yet |

## Time handling

- Input is the **local wall-clock time** at the birth place plus an **IANA timezone name**
  (e.g. `Asia/Kolkata`), resolved via `zoneinfo` + the `tzdata` package.
- Historical offsets come from the IANA database, including India's wartime +06:30
  (1941-10-01 → 1942-05-15 and 1942-09-01 → 1945-10-15).
- A time that fell in a DST gap is **rejected** (`NonexistentLocalTime`).
- A time that happened twice (DST fall-back) is **rejected unless `fold` is given**
  (`AmbiguousLocalTime`, which carries both UTC options for the UI to offer).
- UTC is treated as UT1 for the Julian day (difference < 1 s, negligible).
- A custom `utc_offset_minutes` overrides the zone entirely (for records in Bombay Time,
  Calcutta Time, or war time already converted to IST). It is shown as "(custom)".
- India's 1941–45 War Time is reported as war time, not daylight saving, even though
  tzdata encodes it as DST.

### Birth-time accuracy

| `time_accuracy` | Time used | Window checked |
|---|---|---|
| `exact` | as entered | ±5 min (records are often rounded) |
| `approximate` | as entered | ± the user's choice (default 30 min) |
| `unknown` | 12:00 local | ±12 h (the whole day) |

`reliability` in the chart samples the ascendant and Moon every 5 minutes across the
window. If the ascendant sign can change, `basis` becomes `"moon"` and readings count
houses from the Moon sign (`house_from_moon`), except for `exact` times, which keep the
ascendant but carry a boundary warning. Moon sign or nakshatra changes in the window are
flagged too, since the nakshatra drives dasha timing.

### Known limitation: pre-1955 Indian local times

IANA treats all of India as IST (+05:30) from 1906 on. In reality Calcutta kept its own
time (+05:53:20) until 1948 and Bombay (+04:51) until 1955. Birth records from those
cities in that period may be in local city time. The confirmation screen shows the UTC
offset used, warns about this for pre-1955 Indian births, and lets the user set a custom
offset (e.g. +04:51).

## Coordinates

Latitude north positive, longitude **east positive** (Swiss Ephemeris convention).

## Vimshottari dasha

- **Start:** the lord of the Moon's nakshatra at birth; the share of the nakshatra still to cross is the share of that mahadasha left (the balance).
- **Order and years:** Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17 (120 in all). Antardashas and pratyantardashas split their parent in the same proportions, starting with the parent's own lord.
- **Year length:** 365.25 days. AstroSage adds calendar years instead; the two agree to within two days on every mahadasha boundary in `data/golden_charts` (checked from AstroSage's own Moon, so the test isolates the arithmetic).
- **Sensitivity:** the dasha clock is the Moon. A 1′ error in the Moon moves a 20-year dasha by about 9 days, and ±5 minutes of birth time moves it by about a week. The API reports this as `uncertainty_days`, and `timing_reliable: false` when the Moon changes nakshatra within the birth-time window.
