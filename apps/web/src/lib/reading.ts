import type { NarratedPoint, Narration, Reading, Statement } from "./types";

/** One line on the page and the rules behind it (for "Why this?"). */
export type Point = { key: string; text: string; statements: Statement[] };

export type ReadingView = {
  summary: string;
  groups: { label: string; points: Point[] }[];
  disclaimer: string | null;
  /** True when no model wrote this and the rule texts are shown as they are. */
  quick: boolean;
};

const LABELS = ["For you", "Against you", "Now"] as const;

function fromStatements(statements: Statement[]): Point[] {
  return statements.map((s) => ({ key: s.rule_id, text: s.text, statements: [s] }));
}

/** The rule reading as it is: one line per matched rule. */
export function rulesView(reading: Reading): ReadingView {
  const lists = [reading.strengths, reading.watch_points, reading.current_period];
  return {
    summary: reading.summary,
    groups: LABELS.map((label, i) => ({ label, points: fromStatements(lists[i]) })),
    disclaimer: reading.disclaimer,
    quick: true,
  };
}

/** A written reading: each sentence keeps the statements it cites, so "Why this?" still works. */
export function narrationView(n: Narration): ReadingView {
  if (n.mode === "rules") return rulesView(n.reading);
  const r = n.reading;
  const byId = new Map([...r.strengths, ...r.watch_points, ...r.current_period].map((s) => [s.rule_id, s]));
  const points = (list: NarratedPoint[]): Point[] =>
    list.map((p) => ({
      key: p.rule_ids.join("+"),
      text: p.text,
      statements: p.rule_ids.map((id) => byId.get(id)).filter((s): s is Statement => s !== undefined),
    }));
  const lists = [n.strengths, n.watch_points, n.current_period];
  return {
    summary: n.summary,
    groups: LABELS.map((label, i) => ({ label, points: points(lists[i]) })),
    disclaimer: r.disclaimer,
    quick: false,
  };
}

export const isPossible = (p: Point) => p.statements.some((s) => s.certainty === "possible");
