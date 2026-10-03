# Vedic Astro

A Vedic (sidereal, Lahiri) astrology app that explains *why* each reading says what it
says, by linking every insight to the planetary placement behind it. See [plan.md](plan.md)
for the full build plan.

```
apps/api   FastAPI backend: chart engine (Swiss Ephemeris), rule readings, LLM narration
apps/web   Next.js + Tailwind frontend
data/      golden charts from reference software, used by tests
docs/      calculation conventions and other decisions
```

## Status

- [x] Phase 0: repo, tooling, CI workflows, conventions doc
- [x] Phase 1: chart engine: planets, ascendant, whole-sign houses, nakshatra/pada,
      dignity, combustion, D9, timezone handling, `POST /api/v1/chart`
- [x] Phase 2: place search (Photon, Nominatim fallback, cached), offline timezone lookup,
      birth form with exact/approximate/unknown time, confirmation screen with UTC offset,
      historical-time notes and custom offset, raw chart JSON at `/onboarding`
- [x] Golden charts from Drik Panchang and AstroSage (see `data/golden_charts/README.md`)
- [x] Phase 3: South and North Indian charts, planet table, D9, tap-to-explain glossary
- [x] Phase 4: Vimshottari dasha, `POST /api/v1/dasha`, timeline under the chart
- [x] Phase 5: rule engine (214 rules, five areas), `POST /api/v1/readings`, "Why this?"
- [x] Phase 6: LLM narration with provider fallback, cache and validator,
      `POST /api/v1/readings/{area}/narration`; rule-only text when no provider answers
- [x] Phase 7 (in progress): email/password accounts (Supabase), saved charts with
      consent, "Delete my data", per-user daily AI allowance; see `docs/privacy.md`

## Backend

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate        # Windows; use .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload # http://localhost:8000/docs
```

Print a chart for comparison with reference software:

```bash
python -m app.cli 1990-05-17 14:35 Asia/Kolkata 12.9716 77.5946
```

## Frontend

```bash
cd apps/web
npm install
npm run dev                   # http://localhost:3000/onboarding (needs the API running)
npm test
```

## LLM keys (optional)

Readings are written as prose by free LLM APIs when keys are set; without them the rule
texts are shown as they are. Copy `.env.example` to `.env` at the repo root and add any of
`GEMINI_API_KEY` ([AI Studio](https://aistudio.google.com/apikey)), `GROQ_API_KEY`
([Groq console](https://console.groq.com/keys)) and `OPENROUTER_API_KEY`
([OpenRouter](https://openrouter.ai/settings/keys)). Models and free-tier limits live in
`apps/api/app/llm/providers.yaml`. To check answers against 20 charts with real calls:

```bash
cd apps/api
python -m app.llm.eval
```

Only chart facts (signs, houses, dignities, running dasha) and the matched rules are sent:
never a name, birth date, time or place. Narrations are cached by a hash of exactly that
input in `apps/api/.cache/readings.sqlite3`, so a repeat costs nothing.

## Accounts (Supabase)

Sign-in, saved profiles and charts live in Supabase; the schema and row-level security
policies are in `supabase/migrations/`. The web app reads `NEXT_PUBLIC_SUPABASE_URL` and
`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` from `apps/web/.env.local`; the API only needs
`SUPABASE_URL` (it checks sign-in tokens against the project's public signing keys).

## Third-party services

Place search sends only the typed place name to [Photon](https://photon.komoot.io)
(fallback: [Nominatim](https://nominatim.org)), both OpenStreetMap-based and free with
fair-use limits. Set `GEOCODER_USER_AGENT` to something that identifies you before
deploying. Results are cached in SQLite (`apps/api/.cache/`), so repeat searches never
leave the server. Timezones are resolved offline with `timezonefinder`.

## License

The engine uses Swiss Ephemeris, which is dual-licensed (AGPL or a paid professional
license). Running it as a public service under AGPL means this project's source must be
published under the AGPL as well. See the licensing warning in plan.md.
