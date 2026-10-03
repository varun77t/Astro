import { describe, expect, it } from "vitest";
import { isPossible, narrationView, rulesView } from "./reading";
import type { Narration, Reading, Statement } from "./types";

const st = (rule_id: string, tone: Statement["tone"], certainty: Statement["certainty"] = "sure"): Statement => ({
  rule_id,
  title: rule_id,
  text: `text of ${rule_id}`,
  tone,
  weight: 0.5,
  certainty,
  because: [{ text: `because ${rule_id}`, planets: [], houses: [] }],
  source: "test",
});

const reading: Reading = {
  area: "relationships",
  title: "Relationships",
  basis: "ascendant",
  summary: "Rule summary.",
  strengths: [st("REL-A", "supportive"), st("REL-B", "supportive", "possible")],
  watch_points: [st("REL-C", "cautionary")],
  current_period: [st("REL-D", "supportive")],
  disclaimer: null,
  matched_rule_ids: ["REL-A", "REL-B", "REL-C", "REL-D"],
};

const narration = (mode: Narration["mode"]): Narration => ({
  area: "relationships",
  language: "en",
  mode,
  provider: mode === "llm" ? "groq" : null,
  model: null,
  cached: false,
  summary: "Written summary.",
  strengths: [{ text: "Both strengths in one line.", rule_ids: ["REL-A", "REL-B"] }],
  watch_points: [{ text: "The hard one.", rule_ids: ["REL-C"] }],
  current_period: [{ text: "Now.", rule_ids: ["REL-D"] }],
  reading,
  rules_version: "x",
});

describe("reading views", () => {
  it("shows one line per rule in the quick version", () => {
    const v = rulesView(reading);
    expect(v.quick).toBe(true);
    expect(v.summary).toBe("Rule summary.");
    expect(v.groups.map((g) => g.points.length)).toEqual([2, 1, 1]);
  });

  it("keeps the cited statements behind each written line", () => {
    const v = narrationView(narration("llm"));
    expect(v.quick).toBe(false);
    const [line] = v.groups[0].points;
    expect(line.text).toBe("Both strengths in one line.");
    expect(line.statements.map((s) => s.rule_id)).toEqual(["REL-A", "REL-B"]);
    expect(isPossible(line)).toBe(true); // REL-B depends on the birth time
    expect(isPossible(v.groups[1].points[0])).toBe(false);
  });

  it("falls back to the rule texts when no model wrote it", () => {
    expect(narrationView(narration("rules"))).toEqual(rulesView(reading));
  });
});
