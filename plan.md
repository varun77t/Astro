# Vedic Astrology App: Build Plan

A phase-by-phase plan, architecture, folder structure, and tech stack for a **Vedic-only** (Jyotish) astrology app. Users enter birth details and get chart-based insights on education, career, money, health, and relationships. The whole stack is designed to run on **free tiers**, including the LLM.

---

## 0. Product definition

**One-line pitch:** A Vedic astrology app that explains *why* each reading says what it says, by linking every insight to the planetary placement behind it.

**Scope decisions (locked for v1)**

| Decision | Choice | Reason |
|---|---|---|
| Astrology system | Vedic (sidereal, Lahiri ayanamsa) | Matches the health/education/money use case; dashas give timing |
| House system | Whole sign | Standard in Vedic |
| Node type | Pick **mean** or **true** Rahu once, document it, and stay consistent | Results differ by a small amount; mixing causes confusing mismatches |
| Dasha system | Vimshottari (120-year cycle) | Most widely used |
| Dasha year length | 365.25 days | Pick one convention and document it |
| Chart style | North Indian first, South Indian toggle later | North Indian is the most recognized in India |
| Platform | Web first (responsive PWA) | One codebase, fastest to ship |
| Languages | English first, Hindi and Kannada in a later phase | Content volume is the constraint |

**Out of scope for v1:** Western astrology, marketplace of human astrologers, payments, native mobile apps.

---

## 1. Architecture overview

The app is split into **two layers** so accuracy never depends on the LLM.

```
┌──────────────────────────────────────────────────────────────┐
│                       Next.js Web App                        │
│   Input form · Chart view · Reports · Timeline · Chat · Auth │
└──────────────────────────────┬───────────────────────────────┘
                               │ REST/JSON
┌──────────────────────────────▼───────────────────────────────┐
│                       FastAPI Backend                        │
│                                                              │
│  ┌────────────────────┐     ┌─────────────────────────────┐  │
│  │ 1. CALCULATION     │     │ 2. INTERPRETATION           │  │
│  │ (deterministic)    │────▶│ (rules + LLM narration)     │  │
│  │ Swiss Ephemeris    │     │ Rule matcher → Prompt       │  │
│  │ Houses, nakshatra  │     │ builder → LLM router        │  │
│  │ Dasha, vargas      │     │ → Validator → Cache         │  │
│  └────────────────────┘     └──────────────┬──────────────┘  │
│                                            │                 │
└───────────────┬────────────────────────────┼─────────────────┘
                │                            │
        ┌───────▼───────┐          ┌─────────▼──────────┐
        │ Supabase      │          │ Free LLM providers │
        │ Postgres+Auth │          │ Gemini → Groq →    │
        │ + cache       │          │ OpenRouter (:free) │
        └───────────────┘          └────────────────────┘
```

**Core principles**

1. **The LLM never calculates.** It only turns computed chart facts and matched rules into readable prose.
2. **Every claim is traceable.** Each reading cites rule IDs ("Jupiter in 5th house") that power the "Why this?" feature.
3. **Cache aggressively.** Free LLM tiers are rate-limited, so the same chart + area + language should never hit the LLM twice.
4. **Degrade gracefully.** If every LLM provider is rate-limited, show the rule-based text directly.
5. **Minimize what the LLM sees.** Send chart facts only. Never send name, email, or exact birth place.

---

## 2. Tech stack (all free-tier friendly)

| Layer | Choice | Notes |
|---|---|---|
| Frontend | **Next.js (TypeScript) + Tailwind CSS** | App Router, PWA-ready |
| Chart rendering | **SVG** (hand-written React components) | North and South Indian layouts |
| Backend | **FastAPI (Python 3.11+)** | Python needed for the ephemeris library |
| Astronomy | **pyswisseph** (Swiss Ephemeris) | See licensing warning below |
| Timezone | **timezonefinder + zoneinfo** | Historical timezone and DST handling |
| Geocoding | **Nominatim (OpenStreetMap)** or **Photon** | Free; respect the usage policy (about 1 request/second, set a User-Agent), and cache results |
| Database + Auth | **Supabase** (Postgres + Auth) | Free tier; row-level security for user data |
| LLM | **Gemini free tier → Groq → OpenRouter `:free` models** | Provider router with fallback (section 6) |
| Validation | **Pydantic v2** | Typed request/response and LLM output validation |
| Knowledge base | **YAML/JSON rule files in the repo** | Versioned, reviewable, testable |
| Testing | **pytest** (backend), **Vitest + Playwright** (frontend) | Golden-chart tests are the most important |
| Hosting | Frontend: **Vercel** (Hobby). Backend: a free web-service tier such as **Render** or **Hugging Face Spaces** | Free backends may sleep when idle; verify current terms |
| CI | **GitHub Actions** | Lint, test, deploy |

> **Licensing warning (important):** Swiss Ephemeris is dual-licensed: AGPL or a paid professional license. If you run it as a public network service under AGPL, you must make your source available under AGPL. For a student/open-source project this is fine; if you later want a closed-source commercial product, plan to buy the professional license.

> **Free-tier warning for LLMs:** free-tier terms and limits change often. Check each provider's current docs before relying on a number. Some free tiers may use your prompts to improve their models and may restrict commercial use or certain regions, which is another reason to send only anonymized chart facts.

---

## 3. Folder structure

Monorepo layout:

```
vedic-astro/
├── plan.md
├── README.md
├── .env.example
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── api-ci.yml
│       └── web-ci.yml
│
├── apps/
│   ├── api/                              # FastAPI backend
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── ephe/                         # optional Swiss Ephemeris data files
│   │   ├── app/
│   │   │   ├── main.py                   # FastAPI entrypoint
│   │   │   ├── core/
│   │   │   │   ├── config.py             # env settings
│   │   │   │   ├── logging.py
│   │   │   │   └── security.py           # JWT verify (Supabase)
│   │   │   ├── api/v1/
│   │   │   │   ├── geocode.py            # GET /geocode?q=
│   │   │   │   ├── chart.py              # POST /chart
│   │   │   │   ├── dasha.py              # POST /dasha
│   │   │   │   ├── readings.py           # POST /readings/{area}
│   │   │   │   ├── daily.py              # GET /daily
│   │   │   │   ├── chat.py               # POST /chat
│   │   │   │   └── profiles.py           # CRUD saved profiles
│   │   │   ├── engine/                   # LAYER 1: calculation (no LLM here)
│   │   │   │   ├── ephemeris.py          # Swiss Ephemeris wrapper
│   │   │   │   ├── time_utils.py         # local time → UTC → Julian day
│   │   │   │   ├── houses.py             # ascendant + whole-sign houses
│   │   │   │   ├── nakshatra.py          # nakshatra, pada, lords
│   │   │   │   ├── dasha.py              # Vimshottari mahadasha/antardasha
│   │   │   │   ├── vargas.py             # D9 (Navamsa), D10, etc.
│   │   │   │   ├── strength.py           # dignity, retrograde, combustion
│   │   │   │   ├── yogas.py              # yoga detection
│   │   │   │   ├── transits.py           # current planetary positions
│   │   │   │   └── constants.py          # signs, lords, nakshatras
│   │   │   ├── knowledge/                # the rule base (your real IP)
│   │   │   │   ├── rules/
│   │   │   │   │   ├── education.yaml
│   │   │   │   │   ├── career.yaml
│   │   │   │   │   ├── money.yaml
│   │   │   │   │   ├── health.yaml
│   │   │   │   │   └── relationships.yaml
│   │   │   │   ├── glossary.yaml         # plain-language term explanations
│   │   │   │   └── loader.py
│   │   │   ├── interpret/                # LAYER 2: interpretation
│   │   │   │   ├── rule_matcher.py       # chart facts → matched rules
│   │   │   │   ├── prompt_builder.py     # rules + chart → LLM prompt
│   │   │   │   ├── reading_service.py    # orchestrates a full reading
│   │   │   │   ├── validator.py          # check LLM output vs. chart facts
│   │   │   │   └── guardrails.py         # banned phrases, disclaimers
│   │   │   ├── llm/
│   │   │   │   ├── base.py               # LLMProvider interface
│   │   │   │   ├── gemini.py
│   │   │   │   ├── groq.py
│   │   │   │   ├── openrouter.py
│   │   │   │   ├── router.py             # fallback chain + retry/backoff
│   │   │   │   ├── rate_limiter.py       # per-provider RPM/RPD tracking
│   │   │   │   └── cache.py              # response cache
│   │   │   ├── schemas/                  # Pydantic models
│   │   │   │   ├── birth.py
│   │   │   │   ├── chart.py
│   │   │   │   └── reading.py
│   │   │   └── db/
│   │   │       ├── client.py
│   │   │       └── models.sql
│   │   └── tests/
│   │       ├── golden/                   # known charts + expected output
│   │       ├── test_ephemeris.py
│   │       ├── test_dasha.py
│   │       ├── test_timezone_edge_cases.py
│   │       ├── test_rule_matcher.py
│   │       └── test_llm_router.py
│   │
│   └── web/                              # Next.js frontend
│       ├── package.json
│       ├── next.config.js
│       ├── src/
│       │   ├── app/
│       │   │   ├── page.tsx              # landing
│       │   │   ├── onboarding/page.tsx   # birth-details form
│       │   │   ├── chart/[id]/page.tsx   # chart + planet table
│       │   │   ├── reports/[area]/page.tsx
│       │   │   ├── timeline/page.tsx
│       │   │   ├── daily/page.tsx
│       │   │   ├── chat/page.tsx
│       │   │   └── profile/page.tsx
│       │   ├── components/
│       │   │   ├── chart/
│       │   │   │   ├── NorthIndianChart.tsx
│       │   │   │   ├── SouthIndianChart.tsx
│       │   │   │   └── PlanetTable.tsx
│       │   │   ├── forms/
│       │   │   │   ├── BirthForm.tsx
│       │   │   │   └── PlaceAutocomplete.tsx
│       │   │   ├── reading/
│       │   │   │   ├── ReadingCard.tsx
│       │   │   │   └── WhyThisDrawer.tsx # shows the rules behind a claim
│       │   │   ├── timeline/DashaTimeline.tsx
│       │   │   └── ui/                   # shared primitives
│       │   ├── lib/
│       │   │   ├── api.ts
│       │   │   └── supabase.ts
│       │   └── i18n/                     # en.json, hi.json, kn.json
│       └── tests/
│
├── data/
│   └── golden_charts/                    # reference charts from trusted software
│
└── docs/
    ├── api.md
    ├── rule-writing-guide.md
    ├── calculation-conventions.md        # ayanamsa, node type, dasha year, etc.
    └── privacy.md
```

---

## 4. Data models

**Chart JSON (output of the calculation layer, input to everything else)**

```json
{
  "meta": {
    "ayanamsa": "lahiri",
    "ayanamsa_value": 24.19,
    "house_system": "whole_sign",
    "node_type": "mean",
    "engine_version": "1.0.0",
    "utc": "1999-03-14T04:30:00Z"
  },
  "ascendant": { "longitude": 112.4, "sign": "Cancer", "nakshatra": "Pushya", "pada": 3 },
  "planets": [
    {
      "name": "Moon",
      "longitude": 45.2,
      "sign": "Taurus",
      "degree_in_sign": 15.2,
      "house": 11,
      "nakshatra": "Rohini",
      "pada": 2,
      "retrograde": false,
      "dignity": "exalted"
    }
  ],
  "dasha": { "current_mahadasha": "Jupiter", "current_antardasha": "Saturn", "periods": [] },
  "divisional": { "D9": { "ascendant_sign": "Libra", "planets": [] } }
}
```

**Database tables (Supabase/Postgres)**

```sql
profiles        (id, user_id, label, birth_date, birth_time, time_accuracy,
                 place_name, lat, lon, tz_name, created_at)
charts          (id, profile_id, chart_json, chart_hash, engine_version, created_at)
readings        (id, chart_hash, area, language, rules_version,
                 content_json, provider, created_at)      -- the LLM cache
chat_messages   (id, profile_id, role, content, created_at)
journal_entries (id, profile_id, entry_date, text, tags, created_at)
geocode_cache   (query, lat, lon, tz_name, created_at)
```

Row-level security: every table with `user_id`/`profile_id` is readable only by its owner. `readings` and `geocode_cache` are keyed by hash/query, contain no personal data, and can be shared across users.

---

## 5. Knowledge base (rule) format

Rules are the product. Keep them structured so they are testable and citeable.

```yaml
- id: EDU-5H-JUP-001
  area: education
  title: Jupiter in the 5th house
  when:
    planet: Jupiter
    house: 5
  effect: >
    Supports learning, curiosity, and good mentors. Often favors study of
    teaching, law, finance, or philosophy.
  tone: supportive
  weight: 0.8
  source: "Brihat Parashara Hora Shastra (paraphrased)"

- id: EDU-5L-DEBIL-004
  area: education
  title: Lord of the 5th house is debilitated
  when:
    lord_of_house: 5
    dignity: debilitated
  effect: >
    Focus may need more deliberate effort; structured routines help.
  tone: cautionary
  weight: 0.6
```

**Rule-writing guidelines (go in `docs/rule-writing-guide.md`)**

- Use soft, tendency-based language ("often", "may", "tends to").
- Never predict specific illnesses, death, accidents, or specific investments.
- Every rule has an ID, an area, a weight, and a source note.
- Each rule has at least one unit test with a chart that should trigger it.

---

## 6. Free LLM strategy

**Use a provider router so no single free tier is a single point of failure.**

| Priority | Provider | Good for | Watch out for |
|---|---|---|---|
| 1 | **Google Gemini API (AI Studio key)**, Flash/Flash-Lite models | Best quality and throughput on a free key; also supports JSON output | Free tier has been restricted to Flash-class models; limits have changed several times; free-tier data may be used to improve Google models; check regional and commercial-use terms |
| 2 | **Groq** (free tier) | Very fast responses, good for the chat feature | Per-model request and token caps; model list changes |
| 3 | **OpenRouter `:free` models** | Many models behind one OpenAI-compatible API; good fallback | Small daily request cap on free models; availability varies |
| Last resort | **Rule-based text only** | Always available | Less polished prose |

> Exact limits are changing constantly. Keep them in config (not hard-coded) and read the provider's current rate-limit page before launch.

**How the router works**

```
request → check cache (chart_hash + area + language + rules_version)
        → HIT: return
        → MISS: try provider 1
                 ├─ success → validate → cache → return
                 ├─ 429/timeout → exponential backoff, mark provider cooling down
                 └─ fail → try provider 2 → provider 3 → rule-only fallback
```

**Making free quotas last**

1. **Cache by chart hash.** Same chart + area + language = one LLM call, ever.
2. **Generate per-area, not per-question.** One reading per life area, reused on every visit.
3. **Pre-generate the generic parts.** Planet-in-house explanations and dasha descriptions can be generated once offline and stored, so users only trigger LLM calls for the personalized synthesis.
4. **Keep prompts compact.** Send only matched rules, not the whole knowledge base.
5. **Use a cheaper model for chat, a better one for reports** when providers allow.
6. **Per-user daily chat limit** (for example 10 messages) with a clear message.
7. **Track usage** per provider in the DB so you know when you are near limits.

**Prompt structure (reading generation)**

```
SYSTEM:
You are a Vedic astrology writer. Use ONLY the facts and rules provided.
Do not invent planetary positions. Use tentative language ("tends to", "may").
Do not predict specific illnesses, accidents, death, or investments.
Output valid JSON matching the schema.

USER:
Area: education
Chart facts: { ascendant, relevant planets, houses, current dasha }
Matched rules: [ {id, title, effect, weight}, ... ]
Language: English

Return: {
  "summary": "...",
  "strengths": ["..."],
  "watch_points": ["..."],
  "current_period_note": "...",
  "cited_rule_ids": ["EDU-5H-JUP-001", ...]
}
```

**Validator (runs on every LLM response)**

- JSON parses and matches the schema.
- Every `cited_rule_id` exists in the matched rules.
- Planet and sign names mentioned in the text match the chart (reject if the model invents a placement).
- No banned phrases from `guardrails.py`.
- On failure: retry once with a stricter instruction, then fall back to rule-only text.

**Privacy rules for LLM calls**

- Never send name, email, user ID, or exact birth place.
- Send chart facts only (signs, houses, nakshatras, dasha).
- Log provider and latency, not prompt contents.

---

## 7. Phase-by-phase plan

Timeline assumes one developer working part-time (about 10 to 12 weeks total). Adjust freely.

### Phase 0: Setup and decisions (Days 1 to 3)

**Goals:** repo, tooling, conventions locked.

- [ ] Create the monorepo with the folder structure above
- [ ] Set up Python env (`pyproject.toml`), Next.js app, linters, formatters
- [ ] Create Supabase project (free), GitHub repo, GitHub Actions skeleton
- [ ] Get API keys: Gemini (AI Studio), Groq, OpenRouter
- [ ] Write `docs/calculation-conventions.md` (ayanamsa, node type, dasha year, house system)
- [ ] Gather 8 to 10 **golden charts**: birth data plus expected positions from trusted software (for example Jagannatha Hora or AstroSage), including a few edge cases (see Phase 1)

**Done when:** `git push` triggers CI, and both apps boot locally.

---

### Phase 1: Chart engine (Weeks 1 to 2)

**Goals:** correct planetary positions and ascendant for any birth input.

- [ ] `time_utils.py`: local datetime + place timezone → UTC → Julian day
- [ ] `ephemeris.py`: set sidereal mode (Lahiri), compute Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, with speed and retrograde flag
- [ ] `houses.py`: ascendant via Swiss Ephemeris, whole-sign houses, planet-to-house mapping
- [ ] `nakshatra.py`: nakshatra (27), pada (4), and nakshatra lord for each planet and the ascendant
- [ ] `strength.py`: sign lord, dignity (exalted, own, friendly, enemy, debilitated), combustion
- [ ] `vargas.py`: D9 Navamsa first, others later
- [ ] Golden-chart tests: planets match reference within about 1 arcminute; ascendant sign always matches
- [ ] Timezone edge-case tests: India's historical time changes (including wartime time in the 1940s), places with DST, southern hemisphere, near-midnight births, births near sign boundaries

**Done when:** all golden charts pass and edge-case tests are written.

**Watch out:** a wrong timezone silently ruins the ascendant. Test this harder than anything else. Also decide whether to use Swiss Ephemeris data files or the built-in fallback, and document it.

---

### Phase 2: API and input flow (Weeks 3 to 4)

**Goals:** a user can enter details and get a chart back.

- [ ] FastAPI routes: `POST /chart`, `GET /geocode`
- [ ] Geocoding with Nominatim/Photon, resolve timezone with `timezonefinder`, cache results in `geocode_cache`
- [ ] Pydantic schemas for birth input and chart output
- [ ] Frontend `BirthForm` with `PlaceAutocomplete`
- [ ] "I don't know my exact time" flow: approximate window, plus a clear accuracy warning; fall back to a Moon-sign (Rashi) based reading that does not rely on the ascendant
- [ ] **Confirmation screen** showing resolved place, timezone, and UTC offset before generating the chart
- [ ] Input validation and friendly error messages

**Done when:** a user can go from the form to a raw chart JSON displayed on screen.

---

### Phase 3: Chart visualization (Weeks 4 to 5)

**Goals:** a proper Kundli the user can read.

- [ ] `NorthIndianChart.tsx` (SVG diamond layout; fixed house positions, signs rotate by ascendant)
- [ ] `SouthIndianChart.tsx` (fixed sign boxes) and a style toggle
- [ ] `PlanetTable.tsx`: sign, degree, house, nakshatra and pada, dignity, retrograde marker
- [ ] D9 (Navamsa) chart view
- [ ] Tap/click a planet or house for a plain-language explanation (from `glossary.yaml`)
- [ ] Responsive layout for phones; keyboard and screen-reader labels

**Done when:** the chart visually matches the reference software for every golden chart.

---

### Phase 4: Dasha and timeline (Week 5)

**Goals:** timing, the main reason people use Vedic astrology.

- [ ] `dasha.py`: Vimshottari mahadasha and antardasha (and pratyantar if time permits), starting from the Moon's nakshatra and balance at birth
- [ ] `POST /dasha` returning all periods with start/end dates and the current one
- [ ] `DashaTimeline.tsx`: scrollable timeline with the current period highlighted
- [ ] Tests against golden charts: period boundaries match reference software within a day

**Done when:** current mahadasha/antardasha and boundaries match the reference tool.

---

### Phase 5: Rule engine, no LLM yet (Weeks 6 to 7)

**Goals:** useful readings that work with zero AI.

- [ ] Write `rule_matcher.py`: evaluate rules against a chart JSON
- [ ] Write the first rule sets for **Education** and **Career** (aim for 40 to 60 rules each)
- [ ] Add Money, Health, Relationships after those two are solid
- [ ] `guardrails.py`: banned phrases and mandatory disclaimers
- [ ] `POST /readings/{area}` returning matched rules and a plain template-based reading
- [ ] `ReadingCard.tsx` and `WhyThisDrawer.tsx`, showing each statement with the placement behind it
- [ ] Unit test per rule using a chart that should trigger it

**Done when:** every life-area page shows rule-based text with "Why this?" for each point.

---

### Phase 6: LLM layer (Weeks 7 to 8)

**Goals:** turn rules into natural, personalized prose using free APIs.

- [ ] `llm/base.py` provider interface; implement `gemini.py`, `groq.py`, `openrouter.py`
- [ ] `router.py`: fallback chain, retry with exponential backoff, per-provider cooldown on 429
- [ ] `rate_limiter.py`: track requests per minute and per day in config-driven limits
- [ ] `cache.py` + `readings` table: key = `chart_hash + area + language + rules_version`
- [ ] `prompt_builder.py` and `validator.py` (section 6)
- [ ] Rule-only fallback when all providers fail
- [ ] A small eval set: 20 charts, check that the output cites real rules and never contradicts chart facts
- [ ] Loading and error states in the UI ("Writing your reading…", "Showing the quick version")

**Done when:** readings generate through at least two different providers, repeat visits hit the cache, and the validator rejects a deliberately bad response in tests.

---

### Phase 7: Accounts, profiles, privacy (Week 8 to 9)

**Goals:** users can save charts and trust the app with their data.

- [ ] Supabase Auth (email magic link and Google sign-in)
- [ ] Save multiple profiles (self, family); `profiles` and `charts` tables with row-level security
- [ ] Consent screen for storing birth data; "Delete my data" button that removes the profile and its charts
- [ ] `docs/privacy.md`: what is stored, what is sent to LLM providers (chart facts only), retention
- [ ] Align with India's DPDP Act requirements: purpose, consent, deletion, and clear notice
- [ ] Rate limit API endpoints; verify the Supabase JWT in the backend

**Done when:** a user can sign up, save a chart, come back later, and permanently delete their data.

---

### Phase 8: Daily guidance, transits, and "Ask your chart" (Weeks 9 to 10)

**Goals:** reasons to return daily.

- [ ] `transits.py`: current planetary positions and their house relative to the user's Moon sign and ascendant
- [ ] Daily and weekly guidance generated from the transit and current dasha (cached per sign/day, shared across users with the same Moon sign to save LLM calls)
- [ ] **Chat:** conversation grounded in the saved chart JSON and matched rules; per-user daily limit; same guardrails and validator
- [ ] Student mode: exam-period outlook and study-window suggestions (based on dasha plus transits, framed as reflection, not guarantees)
- [ ] Optional: journal entries so users can look back at how periods played out

**Done when:** daily guidance loads quickly from cache, and chat answers stay consistent with the chart.

---

### Phase 9: Testing, hardening, launch (Weeks 10 to 11)

- [ ] Run full golden-chart and edge-case suites in CI
- [ ] Load test the free-tier backend; set caching headers; handle cold starts with a friendly loading state
- [ ] Accessibility pass (contrast, focus order, labels)
- [ ] Add disclaimers: guidance and tradition, not medical, legal, or financial advice
- [ ] Error monitoring (for example Sentry free tier) and basic analytics
- [ ] Deploy: Vercel (web) plus a free backend host; custom domain if desired
- [ ] **Closed beta with 20 to 50 users**, collecting feedback on accuracy trust, wording, and what they came back for

**Done when:** beta users can complete the full flow unaided, with no accuracy bugs found against reference software.

---

### Phase 10: After launch (backlog)

| Feature | Notes |
|---|---|
| Kundli matching (Ashtakoot, 36-point) | Needs a second profile flow |
| Muhurta finder | Auspicious dates for events |
| Hindi and Kannada | Translate rules and glossary; LLM output language setting |
| More divisional charts (D10, D7, etc.) | Strengthens career and relationship readings |
| Yoga detection library | Adds depth to reports |
| PDF export of reports | Possible paid feature |
| Birth time rectification helper | Based on life events |
| Premium tier / payments | Only after retention is proven |
| Native mobile app | Wrap the PWA first, native later if needed |

---

## 8. Responsible-content guardrails

Build these in from day one, not later.

- Position the app as **guidance and cultural tradition**; astrology is not scientifically validated.
- **Health:** general wellness themes only. Never name diseases, predict illness, or discourage medical care.
- **Money:** general themes only. Never recommend specific investments, trades, or timing of purchases.
- **No fear-based content:** no "doom" predictions, no pressure to buy remedies.
- Always show a short disclaimer on health, money, and timeline pages.
- Keep banned phrases in `guardrails.py` and test them.

---

## 9. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Wrong timezone or birth time → wrong ascendant | Whole reading is wrong | Confirmation screen, golden tests, edge-case tests, clear accuracy warnings |
| Free LLM limits change or quotas run out | Readings fail | Provider router, aggressive caching, rule-only fallback, config-driven limits |
| LLM invents planetary facts | Loss of trust | Ground prompts in chart JSON, validator, cite rule IDs |
| Rule base too thin or generic | Readings feel repetitive | Start narrow (education + career), invest time in rule quality, review with a knowledgeable astrologer |
| Free backend sleeps when idle | Slow first load | Loading state, lightweight health pings, cache chart results |
| Swiss Ephemeris AGPL | Source-sharing obligation | Keep the project open source, or buy the professional license before going closed-source |
| Geocoding rate limits | Autocomplete fails | Cache lookups, debounce input, fall back to an alternative free geocoder |
| Privacy or DPDP compliance | Legal and trust risk | Minimal data, consent, deletion, no personal data to LLMs |
| Scope creep (Western, marketplace, payments) | Never ships | Vedic-only v1; backlog in Phase 10 |

---

## 10. Cost summary (target: ₹0 to start)

| Item | Free option |
|---|---|
| Frontend hosting | Vercel Hobby |
| Backend hosting | Render free web service / Hugging Face Spaces |
| Database + auth | Supabase free tier |
| LLM | Gemini free tier, Groq free tier, OpenRouter `:free` models |
| Geocoding | Nominatim / Photon (cached) |
| Monitoring | Sentry free tier |
| CI | GitHub Actions free minutes |
| Ephemeris | Swiss Ephemeris (AGPL) |

Costs to expect later: a domain name, and possibly a paid backend or LLM tier if you outgrow the free limits.

---

## 11. Suggested milestone checklist

- [ ] **M1 (end of Week 2):** accurate chart JSON for all golden charts
- [ ] **M2 (end of Week 5):** chart UI, planet table, and dasha timeline working end to end
- [ ] **M3 (end of Week 7):** rule-based readings for Education and Career with "Why this?"
- [ ] **M4 (end of Week 8):** LLM-written readings via free providers, cached, validated
- [ ] **M5 (end of Week 9):** accounts, saved profiles, privacy and deletion
- [ ] **M6 (end of Week 10):** daily guidance and grounded chat
- [ ] **M7 (end of Week 11):** closed beta live

---

## 12. First steps to take this week

1. Create the repo and the folder skeleton.
2. Install `pyswisseph`, compute the Sun and Moon for one known birth, and compare with a trusted Kundli tool.
3. Write down your calculation conventions in `docs/calculation-conventions.md`.
4. Collect your first 8 to 10 golden charts.
5. Get your Gemini, Groq, and OpenRouter API keys and make one test call to each.
