---
name: Vedic Astro
description: Vedic astrology that shows its working, set on a ruled exam answer sheet.
colors:
  bone: "#f7f6f3"
  paper: "#ffffff"
  ink: "#111111"
  ink-2: "#2f3437"
  muted: "#6b6a66"
  rule: "#eaeaea"
  rule-strong: "#d9d8d4"
  ruling: "#ebe9e3"
  pen: "#9f2f2d"
  pen-bg: "#fdebec"
  blue: "#1f6c9f"
  blue-bg: "#e1f3fe"
  green: "#346538"
  green-bg: "#edf3ec"
  amber: "#956400"
  amber-bg: "#fbf3db"
typography:
  display:
    fontFamily: "Instrument Serif, serif"
    fontSize: "clamp(3.1rem, 6vw, 5.3rem)"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Instrument Serif, serif"
    fontSize: "clamp(2.1rem, 3.6vw, 3rem)"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Instrument Serif, serif"
    fontSize: "2.2rem"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Geist, Helvetica Neue, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "\"tnum\""
  lede:
    fontFamily: "Geist, Helvetica Neue, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Geist, Helvetica Neue, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 2
  working:
    fontFamily: "Geist Mono, SF Mono, monospace"
    fontSize: "0.85rem"
    fontWeight: 400
    lineHeight: 2
  pen:
    fontFamily: "Kalam, cursive"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.75
  gloss:
    fontFamily: "Tiro Devanagari Sanskrit, serif"
    fontSize: "0.9em"
    fontWeight: 400
  pill:
    fontFamily: "Geist, Helvetica Neue, sans-serif"
    fontSize: "0.68rem"
    fontWeight: 600
    letterSpacing: "0.05em"
rounded:
  tick-box: "3px"
  focus: "4px"
  button: "6px"
  surface: "8px"
  pill: "9999px"
spacing:
  line: "2rem"
  margin-sm: "3rem"
  margin-lg: "6rem"
  section-sm: "4rem"
  section-lg: "6rem"
  question-gap: "3.5rem"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.button}"
    padding: "0.8rem 1.25rem"
  button-primary-hover:
    backgroundColor: "#333333"
    textColor: "{colors.paper}"
  button-primary-disabled:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.paper}"
  button-compact:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.button}"
    padding: "0.5rem 1rem"
  link:
    textColor: "{colors.ink}"
  answer-line:
    textColor: "{colors.ink}"
    rounded: "0"
    padding: "0.35rem 0.1rem"
    width: "100%"
  tick-option-box:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.tick-box}"
    size: "24px"
  pill-exalted:
    backgroundColor: "{colors.green-bg}"
    textColor: "{colors.green}"
    typography: "{typography.pill}"
    rounded: "{rounded.pill}"
    padding: "0.1rem 0.5rem"
  pill-own:
    backgroundColor: "{colors.blue-bg}"
    textColor: "{colors.blue}"
    typography: "{typography.pill}"
    rounded: "{rounded.pill}"
    padding: "0.1rem 0.5rem"
  pill-debilitated:
    backgroundColor: "{colors.pen-bg}"
    textColor: "{colors.pen}"
    typography: "{typography.pill}"
    rounded: "{rounded.pill}"
    padding: "0.1rem 0.5rem"
  place-listbox:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.surface}"
  place-option-active:
    backgroundColor: "{colors.bone}"
    textColor: "{colors.ink}"
    padding: "0.625rem 0.75rem"
---

# Design System: Vedic Astro

## Overview

**Creative North Star: "The Worked Answer Sheet"**

Every screen is a page of a ruled exam paper on which the chart is solved in front of the reader. The sheet is warm bone, ruled at a fixed pitch, with one pale red margin rule down the left. Questions are set in a tall editorial serif; the working beneath them is printed in a plain grotesque and a monospace for arithmetic and positions. A teacher's red pen marks the paper: question numbers in the margin, ticks against correct steps, short notes, a crossed-out unknown. Nothing on the sheet is boxed for decoration; the ruling and the margin are the structure.

The world is light-only (`color-scheme: light`); there is no dark theme. Density is that of a well-kept exam script: generous vertical space between questions, tight rhythm within an answer, every answer line snapped to the 2rem ruling. Colour is almost entirely monochrome; red pen is the only voice that marks, and pastel status tints only label dignities.

Motion is handwriting. Lines are revealed left to right as if written, ticks are drawn as strokes, later answers write themselves in at the reader's scroll pace, and the unknown is struck through. With reduced motion requested, the whole page is static and complete.

**Key Characteristics:**
- Ruled bone sheet at a 2rem pitch with a single pale-red margin rule.
- Instrument Serif questions, Geist working, Geist Mono arithmetic, Kalam red pen for marking only.
- Question numbers live in the margin, outside the text column.
- Answers sit on lines, never in cards; inputs are underlines, not boxes.
- Red-pen SVG ticks, crosses and strikes are the only ornaments.
- Motion writes, draws and strikes; it never bounces or floats.

## Colors

A warm monochrome paper with one red pen and three pastel status tints.

### Primary
- **Charcoal Print** (ink): headings, answer text, the primary button fill, focus outlines, and the firmed-up underline of a focused answer line.
- **Teacher's Red Pen** (pen): marking only. Margin question numbers, ticks, crosses, strike lines, short hand notes, the active step underline, error text and the invalid underline of an answer line, the input caret. At 30% opacity it draws the margin rule; at 70-80% it draws strikes and the circled score.

### Secondary
- **Ledger Green** (green, on green-bg): the "exalted" dignity pill.
- **Fountain Blue** (blue, on blue-bg): "own" and "moolatrikona" dignity pills and the retrograde "R" mark.
- **Ochre** (amber, on amber-bg): the combust "C" mark; amber-bg is also the text selection colour.
- **Pen Wash** (pen-bg): the "debilitated" dignity pill background, under pen text.

### Neutral
- **Warm Bone** (bone): the page, the sticky header (at 90% with backdrop blur), the footer, the active row of the place listbox.
- **Clean Paper** (paper): the few surfaces that sit on top of the sheet: the place listbox, the raw JSON block, the tick-box square.
- **Graphite** (ink-2): default body text.
- **Pencil Grey** (muted): labels, step numbers, captions, placeholders, struck-through words, date-input separators.
- **Ruling** (ruling): the horizontal page rules.
- **Hairline** (rule): header and footer borders, popover borders.
- **Firm Hairline** (rule-strong): section dividers (at 70%), resting answer-line underline, table header rule, link underline colour, scrollbar thumb.

### Named Rules
**The Red Pen Rule.** Red marks the paper; it never prints on it. Pen colour is used for marks, notes, errors and the margin rule, never for body copy, buttons or fills.

**The Status-Only Pastels Rule.** Green, blue and amber appear only as dignity and planet-state labels. They never decorate, illustrate or theme a section.

## Typography

**Display Font:** Instrument Serif (with serif)
**Body Font:** Geist (with Helvetica Neue, sans-serif)
**Label/Mono Font:** Geist Mono (with SF Mono, monospace)
**Marking Font:** Kalam (with cursive)
**Gloss Font:** Tiro Devanagari Sanskrit (with serif)

**Character:** A condensed, high-contrast serif asks the question; a neutral grotesque and a monospace do the working; a teacher's hand marks it. Body text uses tabular numerals throughout so degrees and times align.

### Hierarchy
- **Display** (Instrument Serif 400, clamp(3.1rem, 6vw, 5.3rem), 1.05, -0.02em): the landing H1 only. Onboarding step titles use clamp(2.8rem, 6vw, 4.4rem) and the closing call clamp(2.6rem, 5.5vw, 4.6rem).
- **Headline** (Instrument Serif 400, clamp(2.1rem, 3.6vw, 3rem)): question headings on the landing, max 18ch.
- **Title** (Instrument Serif 400, 1.9rem to 2.2rem): form questions and legends in onboarding.
- **Body** (Geist 400, 1rem, 1.6): prose under a question, max 46ch. Ledes run 1.125rem at 34ch to 52ch.
- **Label** (Geist 400, 0.875rem, muted): row labels in the working, set on the ruling pitch.
- **Working** (Geist Mono, 0.8rem to 0.95rem): time arithmetic, degrees, offsets, coordinates, step numbers "(1)". Table column heads use Geist Mono 0.7rem uppercase at 0.06em tracking.
- **Pen** (Kalam 400, 1.125rem; margin numbers 1rem to 1.25rem): marks and short notes only.
- **Gloss** (Tiro Devanagari Sanskrit, 0.9em, muted): Devanagari gloss after a Jyotish term (Lagna, Rashi, Nakshatra).
- **Pill** (Geist 600, 0.68rem, 0.05em, uppercase): dignity status.

### Named Rules
**The Marking Hand Rule.** Kalam is for question numbers, ticks, short notes and marker labels ("Note", "Marked", "Ans."). When a note grows into a sentence that must be read, the label stays in pen and the sentence is printed in Geist beside it.

**The Serif Asks Rule.** Instrument Serif is reserved for questions and step titles. Answers are never set in the serif.

## Layout

The sheet is a full-bleed ruled background; content sits in a centred column (max 72rem) indented to the right of the margin rule at every width: 3rem left / 1rem right on mobile, 6rem left / 1.5rem right from 640px. The margin rule sits at 2rem on mobile and 4.5rem from 640px. Question numbers hang in that margin (absolute, about 2.75rem to 5rem left of the column).

From 1024px, each question is a 5/12 : 7/12 split: the question and its prose on the left, the worked answer on the right; below that it stacks. Sections are separated by a firm hairline and 4rem to 6rem of vertical padding. Within an answer, every line takes the ruling pitch as its line height (2rem) so text sits on the rules. Working rows use a fixed grid: step number, muted label (hidden below 640px, folded inline), answer. Onboarding uses a single 48rem column for questions, with 3.5rem between questions, and returns to the 5/12 : 7/12 split for the chart.

**The On-The-Line Rule.** Answer text, table rows and working rows take `line-height: var(--line)` or `height: var(--line)`. If it is an answer, it sits on a rule.

## Elevation & Depth

The sheet is flat. Depth comes from paper on paper: the ruling, the margin, hairlines and the slightly whiter paper of a popover. There is exactly one shadow, on the floating place listbox, so a dropdown reads as a slip laid on the page. The sticky header separates by a hairline and a 90% bone fill with backdrop blur, not a shadow.

### Shadow Vocabulary
- **Laid Slip** (`box-shadow: 0 18px 40px -18px rgba(17,17,17,0.18)`): floating listboxes only.

### Named Rules
**The Flat Sheet Rule.** Nothing on the sheet casts a shadow except a floating slip that sits above it.

## Shapes

Mostly square and lined. Answer inputs have no corners at all (an underline). The tick box is a near-square (3px). Buttons are gently rounded (6px); floating slips and the raw-data block 8px; status pills fully round. The hand marks bring the only curves: the round-capped tick stroke, the cross, a slightly rotated strike line (-2deg), and a circled score ring (2px pen border at 70%, rotated -4deg). Focus outlines are 2px ink, offset 3px, with a 4px radius.

## Components

### Buttons
Plain, dark and confident; one kind of button.
- **Shape:** gently rounded (6px).
- **Primary:** charcoal ink fill, white Geist 500 text, 0.8rem x 1.25rem padding, optional inline arrow (16px stroke SVG). A compact size (0.5rem x 1rem, 0.875rem text) is used in the header and inline tools.
- **Hover / Focus:** fill lightens to #333 over 200ms; press scales to 0.98 over 120ms; focus is the global 2px ink outline.
- **Disabled:** muted fill with a progress cursor while working.
- **Pairing:** a primary button is usually followed by a short Kalam pen note at 1.125rem ("free, about a minute").

### Links
- **Style:** ink text, underline in firm hairline offset 4px; the underline darkens to ink on hover (200ms). Used for secondary actions ("Back", "Enter coordinates", "Edit") in place of a second button style.

### Chips (status pills)
- **Style:** fully round, pastel tint background with its matching deep text, 0.68rem semibold uppercase. Green for exalted, blue for own and moolatrikona, pen wash for debilitated. Other dignities are printed as plain muted text; missing values are a firm-hairline dash.

### Inputs / Fields
- **Style:** the answer line. No box and no radius; transparent background, 1px firm-hairline underline, 1.125rem ink text, red-pen caret.
- **Focus:** the underline firms to ink and thickens (1px ink underline plus a 1px ink box-shadow below).
- **Error:** underline turns pen red; the message below is pen-red Geist 0.875rem led by a red-pen cross.
- **Native date/time:** separators muted, calendar indicator at 45% rising to 90% on hover or focus.
- **Choice (tick one):** a 24px paper square with an ink-2 border (3px radius); choosing draws a red-pen tick over it (stroke-dashoffset, 300ms ease-out).

### Navigation
- **Header:** sticky slim bar on bone at 90% with backdrop blur and a hairline bottom; wordmark "Vedic Astro" in Geist semibold, tight tracking, plain text with no logo; a compact primary button on the right.
- **Step progress:** a row of mono step numbers and Geist labels; inactive steps muted, the current step ink with a 2px pen underline offset 6px.

### Place listbox
A floating slip of paper under the place answer line: paper background, hairline border, 8px radius, Laid Slip shadow, max 20rem tall. Each option prints the place name in ink and its time zone in mono muted at the right; the active option is shaded bone.

### Worked answer (signature)
The answer block: a muted mono step number "(n)", a muted label, then the working on the ruling pitch, with red-pen ticks against correct steps and a Kalam note citing the cause. Unknowns are printed muted and struck through by a red line drawn across exactly the struck words. A marker's note pairs a pen label with printed Geist text. Jyotish terms carry a Devanagari gloss.

### Chart table
One row per graha at the ruling pitch, no cell borders, a single firm-hairline rule under the uppercase mono column heads. Names in Geist 500 ink, degrees and houses in mono right-aligned, retrograde and combust as tiny mono letters in blue and amber, dignity as a pill.

### Motion
Exponential ease-out (`expo.out`), "like ink meeting paper". Every animation is registered under `(prefers-reduced-motion: no-preference)`; reduced motion gets a static, complete page and 0ms transitions.
- **Write:** `clip-path: inset(0 100% 0 0)` to `inset(0 0% 0 0)`, left to right, 0.85s power2.inOut, staggered 0.3s.
- **Draw:** ticks are SVG paths with `pathLength=1`, drawn from stroke-dashoffset 1 to 0 (0.4s to 0.5s power2.out).
- **Scrub:** later answers write, strike (scaleX 0 to 1 from the left) and tick as the reader scrolls (ScrollTrigger, top 80% to bottom 62%, scrub 0.6).
- **Settle:** headings and prose rise 14px to 22px and fade in (0.8s to 1.1s), batched on scroll (ScrollTrigger.batch, once).

## Do's and Don'ts

### Do:
- **Do** set every answer, working row and table row on the 2rem ruling pitch.
- **Do** put question numbers in Kalam red pen in the margin, outside the text column.
- **Do** mark correct steps with the drawn red-pen tick SVG and unknowns with the red strike line.
- **Do** use Geist Mono for any time, offset, degree, coordinate or step number.
- **Do** gloss Jyotish terms with Tiro Devanagari Sanskrit in muted at 0.9em.
- **Do** register every animation under `(prefers-reduced-motion: no-preference)` and make the reduced-motion page complete.
- **Do** use the answer-line underline for text inputs and the ruled tick box for single choices.

### Don't:
- **Don't** set body copy or long sentences in Kalam; pen notes stay short, and readable content is printed in Geist.
- **Don't** use pen red for buttons, fills, links or headings.
- **Don't** box the working in cards or bordered panels; boxes are kept for floating slips and the raw-data block.
- **Don't** add shadows to anything resting on the sheet.
- **Don't** use green, blue or amber outside status labels.
- **Don't** add a dark theme; the paper is light-only.
- **Don't** introduce a second button style; secondary actions are underlined links.
