---
version: 1
slug: "apps-web-src-app-page-tsx"
primary_target: "apps/web/src/app/page.tsx"
related_targets: ["apps/web/src/app/onboarding/page.tsx"]
---

# Landing + onboarding surface brief

Scope: `/` (Persuade) and `/onboarding` (Operate: birth form, confirmation, chart result).
Audience: Indians 18–30, skeptical of fluff. Action: start a chart. Proof on hand: real
engine output for a labelled sample birth (9 Mar 2002, 07:45 IST, Pune); no users,
testimonials or benchmarks exist. Reading wording is illustrative until Phase 5.
Constraint: user-pinned minimalist palette (warm monochrome, editorial serif, pastel
accents, 1px rules) plus GSAP ScrollTrigger motion.

## Direction contract

THESIS: The page is a worked answer, not a pitch: the chart is solved step by step on
the page and every conclusion is traced to the line that produced it. It refuses the
category default of a cosmic hero over three feature cards.

OWN-WORLD: A ruled exam sheet on warm bone (#F7F6F3): 2rem rules (#EBE9E3), one pale-red
margin rule. Printed ink in charcoal; Instrument Serif for questions, Geist for working,
Geist Mono for arithmetic and positions, Kalam in red-pen (#9F2F2D) only for marking:
question numbers, ticks, notes. Pastel status pills. Working is never boxed; the
ruling and the margin structure the page. Devanagari glosses for Jyotish terms.

STORY: The visitor reads Q1 and its worked answer, sees that each reading line cites a
placement, learns the product is honest about vague birth times (Q2), how the
arithmetic is checked (Q3) and who sees their details (Q4), then starts their own
paper. Onboarding continues the paper: questions answered on rules, "check your
working" before the chart, the chart returned as a marked answer.

FIRST VIEWPORT: Left 5/12: red "Q1." in the margin, H1 "Show your working." in
Instrument Serif near 5rem, a 34ch subline, black "Calculate my chart" button with a
red hand note beside it. Right 7/12: "Ans." then (1) time arithmetic, (2) positions,
(3) rule matched with a tick, (4) reading line with a tick and a red note citing
Venus exalted in the 1st. Slim header: wordmark plus the same action.

FORM: Exam answer sheet, "show your working". Position 1 on my grounded list
(Impeccable's pick, chosen by the user after seeing three built prototypes). Seed
c5d71eb4. Signature motion: the answer writes itself in line by line, ticks are drawn
in red, later answers scrub in with scroll, the unknown Lagna is struck through.
Reduced motion shows everything static.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
