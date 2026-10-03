# Rule-writing guide

Rules are the product. Each one turns a placement into a line of the reading, and the
placement it rests on is what the reader sees under "Why this?". They live in
`apps/api/app/knowledge/rules/<area>.yaml`, one file per life area.

## A rule

```yaml
- id: EDU-5H-JUP                  # AREA-WHAT, unique; the prefix must match the file
  title: Jupiter in the 5th house # shown in "Why this?"
  when: {planet: Jupiter, house: 5}
  effect: Strong for learning. Curiosity and good teachers come together.
  tone: supportive                # supportive | cautionary | neutral
  weight: 0.8                     # 0–1: how much it matters, and the sort order
  source: Parashari house reading (BPHS, paraphrased)
  group: edu-jupiter              # optional: of several matches in a group, only the strongest shows
  needs: lagna                    # optional: skip when houses are counted from the Moon
  test: {lagna: Aries, Jupiter: Leo}   # a chart that must trigger it (see Tests)
```

Cautionary rules become "watch points"; supportive and neutral ones become strengths.
Rules that read the running dasha (`period:`) go to the "Now" note instead.

## Voice

Readings are **frank**. Say what the tradition reads in a placement, in plain words,
hard ones included: delays, friction in marriage, losses, health troubles, interrupted
studies. Don't soften a hard placement into self-help advice, and don't hedge every line.
The reader decides what to believe; the page says once that this is tradition.

- One or two short sentences, at most 180 characters. Second person.
- Name the effect, then (optionally) the shape it takes: "Saturn weighs on learning. Studies
  feel like hard work, and steady effort beats talent here."
- Named yogas lead with their name: "Gaja Kesari yoga. …"
- No jargon the glossary can't explain. No numbers.
- `source` says where the reading comes from, honestly. Use "(paraphrased)" for the classics
  and "Common Jyotish teaching" when it's widely taught but not from one text.

### Limits

`app/interpret/guardrails.py` fails the tests when a rule says any of these:

- predicts death, lifespan, an accident or an injury;
- names a specific illness (general "health problems" or "low stamina" are fine);
- tells anyone to skip a doctor or medication;
- recommends a specific investment, purchase or bet;
- sells remedies (gemstones, pujas, yantras);
- claims certainty ("definitely", "guaranteed", "for sure").

Health and money readings always carry their area's `disclaimer`.

## Conditions

A `when` block is one condition, or a list (all must hold).

**A planet**, picked by one of `planet: Jupiter`, `lord_of: 5` (the ruler of the 5th),
or `period: maha | antar` (the planet whose dasha is running), then tested with:

| key | example | holds when |
|---|---|---|
| `is` | `is: [Mercury, Jupiter]` | the subject is one of these (for `lord_of` and `period`) |
| `house` | `house: 5`, `[1, 4]`, `kendra` | it sits in one of these houses |
| `from` | `from: moon` | count `house` from the Moon instead of the reading's basis |
| `sign` | `sign: [Leo, Aries]` | it sits in one of these signs |
| `dignity` | `dignity: strong` | exalted, moolatrikona, own, friendly, neutral, enemy, debilitated; `strong` = exalted/moolatrikona/own, `weak` = debilitated |
| `retrograde`, `combust` | `combust: true` | |
| `with`, `not_with` | `with: Sun`, `with: malefic` | another planet shares its sign |
| `with_lord_of` | `with_lord_of: 9` | it shares a sign with the ruler of that house |
| `aspected_by` | `aspected_by: Jupiter` | that planet's drishti falls on it |
| `rules` | `rules: [5, 9]` | it rules one of these houses |
| `nakshatra` | `nakshatra: Rohini` | |
| `d9_sign`, `d9_dignity` | `d9_dignity: [exalted, own]` | in the navamsa |
| `vargottama` | `vargottama: true` | same sign in D1 and D9 |

**A house**: `house: 7` with `has: Venus | benefic | [..]`, `empty: true`, or `aspected_by`.

**Others**: `lagna: [Taurus, Libra]` (only on a Lagna-based reading), `exchange: [9, 10]`
(the two rulers sit in each other's signs), and `all: [..]`, `any: [..]`, `not: {..}`.

House sets: `kendra` 1 4 7 10, `trikona` 1 5 9, `dusthana` 6 8 12, `upachaya` 3 6 10 11.
Groups: `benefic` is Jupiter, Venus, Mercury, and the Moon when waxing; `malefic` is the Sun,
Mars, Saturn, Rahu, Ketu, and the Moon when waning. Aspects are whole-sign: every planet
aspects the 7th sign from itself, Mars also the 4th and 8th, Jupiter the 5th and 9th, Saturn
the 3rd and 10th. Rahu and Ketu cast no aspects here.

## Houses from the Moon

When the birth time can't fix the Lagna, every house is counted from the Moon's sign
(Chandra lagna) and the reasons say so ("in the 5th house from your Moon"). Two things follow
automatically: a test that puts the Moon itself in a house never holds (it's always in the
1st from itself), and `lagna:` conditions never hold. Add `needs: lagna` to a rule that makes
no sense from the Moon.

## Sure or possible

Each matched rule is re-tested across the birth-time window (every 10 minutes, and at both
edges). If it holds throughout, it's **sure**; if a different time inside the window would
undo it, it's **possible** and the page marks it. A period rule is only sure when the dasha
couldn't have changed within the dates' own uncertainty.

## Every area needs

- four `summary` lines: `supportive`, `mixed`, `cautionary`, `quiet` (chosen by the balance of
  matched weights);
- one fallback `{period: maha}` rule with weight 0.1, in the same group as the area's other
  main-period rules, so the "Now" note always has something to say.

## Tests

`apps/api/tests/test_rules.py` runs every rule:

- its `test:` chart must trigger it and give at least one reason;
- its title and effect must pass the guardrails.

The test chart starts from a fixed layout (Lagna Aries; Sun Sagittarius, Moon Aquarius, Mars
Gemini, Mercury Capricorn, Jupiter Virgo, Venus Aquarius, Saturn Taurus, Rahu Libra, Ketu
Aries). Name only what the rule needs: `Jupiter: Leo` puts it at 15°, `"Virgo 28 R"` sets the
degree and retrograde, naming Rahu moves Ketu opposite, `basis: moon` drops the Lagna, and
`period: {maha: Jupiter, antar: Saturn}` sets the running dasha.

```bash
cd apps/api && .venv/Scripts/python -m pytest tests/test_rules.py -q
```
