# Golden charts

Reference charts used by `apps/api/tests/test_golden_charts.py`. They are the main
guard against calculation regressions, so the expected values **must come from
independent, trusted software**, never from this app's own output.

## Adding one

1. Copy `_template.json` to a new file, e.g. `bangalore-1990.json` (files starting with `_` are ignored).
2. In the reference software, set the same conventions as `docs/calculation-conventions.md`:
   - Ayanamsa: **Lahiri** (Chitrapaksha)
   - Rahu/Ketu: **mean** node
   - Houses: doesn't matter for longitudes, but whole-sign for the house check
3. Enter the birth data **with the same timezone offset** the IANA zone gives (check the
   UTC offset that `python -m app.cli ...` prints). Reference tools sometimes default to
   a different historical offset, especially for India before 1955.
4. Copy the ascendant and all nine planet longitudes into `expected`. Accepted formats:
   `"Taurus 15:12:05"`, `"Taurus 15°12'05\""`, `"15 Ta 12' 05.12\""` (Jagannatha Hora style),
   or an absolute sidereal longitude in degrees like `45.2014`.
5. Optionally add `nakshatras` for the Moon and ascendant lord.
6. Run `pytest tests/test_golden_charts.py -v` from `apps/api`.

Compare side by side with:

```bash
python -m app.cli 1990-05-17 14:35 Asia/Kolkata 12.9716 77.5946
```

## Coverage to aim for (8–10 charts)

- [x] 2–3 ordinary modern Indian births (`bengaluru-1990`, `pune-2002`, `delhi-1985`)
- [x] India 1942–1945 (wartime +06:30) (`mumbai-1943`)
- [x] A birth in a DST zone in summer (`london-1995`, `newyork-1979`)
- [x] Southern hemisphere (`sydney-2000`, January, AEDT)
- [x] Birth within 15 minutes of midnight (`chennai-1998`, 23:52)
- [x] A planet within 30' of a sign boundary (`mumbai-1943` Venus 9' into Cancer; `sydney-2000` Venus on the line)
- [ ] Moon within 30' of a nakshatra boundary
- [x] Retrograde planets (most charts)

## The current set (collected 2026-10-03)

- **Planets** come from Drik Panchang's sidereal planetary positions page (Lahiri, mean node).
  They agree with this engine to within 41″. Drik's values sit a few to 41″ lower, varying
  with the date, which looks like a slightly different Lahiri/nutation convention.
- **Ascendants** come from AstroSage's free kundli (N.C. Lahiri), entered with the exact
  coordinates (to the arcminute) and UTC offset stored in each file. They agree to within 0.5′.
- **Drik Panchang's ascendant is not used.** It runs ahead of both this engine and AstroSage
  by about `longitude × 0.00274°` of sidereal time (as if longitude were scaled by the
  solar-to-sidereal ratio): 10–20′ for Indian cities, 20′ for Sydney, −11′ for New York.
  Matching it would make the engine wrong.
- `sydney-2000` has Venus within 40″ of the Scorpio/Sagittarius boundary, and the two
  references put it in different signs. Only the longitude is checked; treat the sign of
  any planet that close to a boundary as uncertain.
- Each file's `birth.expected_utc_offset` is asserted too, so a time-zone regression fails
  as an offset error rather than as a vague "Moon off by 30′".
- Each file's `dasha` block holds AstroSage's Vimshottari mahadasha end dates (and, for
  `newyork-1979`, the antardashas of the Sun mahadasha) with the Moon AstroSage used.
  `tests/test_dasha.py` feeds that Moon into our dasha code, so it checks the arithmetic on its
  own; boundaries agree within two days (AstroSage adds calendar years, we use 365.25-day years).

## Known source of disagreement

The IANA database treats all of India as `Asia/Kolkata` (IST) from 1906 on (apart from
the wartime period). Historically, **Calcutta kept its own local time until 1948 and
Bombay until 1955**. A Bombay birth in 1950 recorded in "Bombay Time" (+04:51) will look
39 minutes off. That is a time-input problem, not an engine bug. The confirmation screen shows
the UTC offset used; the API accepts `utc_offset_minutes` for such records, though the app no
longer offers a way to enter it.
