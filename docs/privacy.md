# Privacy

What Vedic Astro stores, what it sends elsewhere, and how to delete it. Written to match
India's Digital Personal Data Protection Act, 2023: a clear purpose, consent before storing,
and deletion on request.

## Without an account

Nothing about you is stored. The birth date, time and place you enter go to our API to
calculate the chart and are not kept. Two caches hold no personal data:

- **Place search:** the typed place name and the matching public places, so repeat searches
  don't go to OpenStreetMap again.
- **Written readings:** keyed by a hash of chart facts (signs, houses, dignities) and the
  matched rules. Anyone with the same placements shares the same entry.

## With an account

| What | Why | Where |
|---|---|---|
| Email and a password hash | To sign you in | Supabase Auth (Mumbai region) |
| For each saved chart: a label you choose, birth date, time, how sure you are of the time, place name and coordinates, time zone | So you can come back to the chart | Supabase Postgres, `profiles` table |
| The calculated chart | To list your charts quickly | `charts` table |
| When you agreed to storing it, and which wording you agreed to | Proof of consent | `profiles.consented_at`, `consent_version` |

Nothing is saved until you tick the consent box on the chart page. Row-level security in the
database means each account can read and change only its own rows; the app's public key
can't reach anyone else's.

## What goes to AI services

Readings are written by free LLM APIs (Google Gemini, Groq). They receive **chart facts and
matched rules only**: Lagna and planet signs, houses, dignities, the running dasha and when it
ends. Never a name, email, birth date, birth time or place. On free tiers, these providers
may use what they receive to improve their models; that is why nothing identifying is sent.
Logs record which provider answered and how fast, never what was sent.

## Deleting

- **One chart:** "Delete" next to it on Your charts. The birth details and the stored chart
  are removed at once.
- **Everything:** "Delete my account and data" on Your charts. The account, every saved chart
  and all birth details are removed permanently (one database transaction; nothing is kept
  in a "deleted" state).

Supabase keeps its own database backups for a limited period on the free plan; deleted rows
leave those as the backups expire.

## Limits on use

To stop one visitor using up everyone's free AI quota, the API counts fresh AI-written
readings per signed-in account, or per IP address for visitors, per day. The counts are kept
in memory only and reset daily.
