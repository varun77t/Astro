# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Young Indians, roughly 18 to 30: students and early-career people curious about what
their chart says about education, career, money, health, and relationships, and about
timing (dasha periods, exam seasons). Comfortable with apps, skeptical of fluff and of
readings that just assert things.

## Product Purpose

A Vedic (sidereal, Lahiri) astrology web app. The user enters birth details and gets a
chart plus readings per life area. Success: the user trusts the chart is calculated
correctly, understands why each reading says what it says, and comes back for timing
and daily guidance.

## Positioning

Every insight shows its working: each reading links to the planetary placement and rule
behind it ("Why this?"). The calculation layer is deterministic (Swiss Ephemeris), and
the LLM only narrates matched rules; it never calculates.

## Operating Context

- Flow today: birth details (date, time with exact / approximate / unknown accuracy,
  place search) -> confirmation of timezone and UTC offset -> chart.
- Many users will not know an exact birth time; the product falls back to Moon-sign
  (Rashi) readings and says so.
- Historical Indian time quirks (WWII +06:30, Bombay/Calcutta local time) are surfaced
  on the confirmation screen.

## Capabilities and Constraints

- Built: chart engine, timezone handling, place search, birth form, confirmation screen,
  South/North Indian chart with D9 and tap-to-explain, dasha timeline, rule-based readings
  for five life areas. Not yet built: LLM narration, accounts, daily guidance, chat.
- Runs on free tiers (Vercel, Render/HF Spaces, Supabase, free LLM APIs).
- English first; Hindi and Kannada later.
- Swiss Ephemeris is AGPL; the project is intended to be open source.

## Brand Commitments

- "Vedic Astro" is a working title: plain text, no logo or mark yet.
- Frank, not comforting: readings say plainly what the tradition reads in the chart,
  hard placements included; the user decides what to believe. Limits: no predicting
  death, no naming a specific illness or accident, never discourage medical care, no
  specific investment calls, no selling remedies, no claims of certainty.

## Evidence on Hand

- Real calculation behaviour and test cases (apps/api/tests), conventions in
  docs/calculation-conventions.md.
- No users, testimonials, press, or accuracy benchmarks yet. Do not invent any.

## Product Principles

1. Show the working: every claim is traceable to a placement or rule.
2. Correct before clever: calculation accuracy and honest timezone handling come first.
3. Honest about uncertainty: say when the birth time cannot support a reading.
4. Free and private: no fees, no data selling, no personal data to LLM providers.
