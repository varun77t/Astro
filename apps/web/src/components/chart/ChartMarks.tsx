import { formatDegree } from "@/lib/format";
import type { ChartMark, LagnaMark } from "@/lib/kundli";

export type Selection = { kind: "planet"; name: string } | { kind: "house"; sign: string } | { kind: "lagna" } | null;

const TINT: Record<string, string> = {
  exalted: "bg-green-bg text-green",
  moolatrikona: "bg-blue-bg text-blue",
  own: "bg-blue-bg text-blue",
  debilitated: "bg-pen-bg text-pen",
};

const NODES = new Set(["Rahu", "Ketu"]);

function describe(mark: ChartMark): string {
  const parts = [mark.name];
  if (mark.degree !== null) parts.push(formatDegree(mark.degree));
  if (mark.dignity && TINT[mark.dignity]) parts.push(mark.dignity);
  if (mark.retrograde && !NODES.has(mark.name)) parts.push("retrograde");
  if (mark.combust) parts.push("combust");
  if (mark.doubt) parts.push("sign uncertain");
  return parts.join(", ");
}

/** A graha written into the chart: abbreviation, state letters, and a pen "?" when its sign is in doubt. Degrees live in the table. */
export function PlanetLabel({ mark, selected, onSelect }: { mark: ChartMark; selected: boolean; onSelect: () => void }) {
  const tint = (mark.dignity && TINT[mark.dignity]) || "text-ink";
  return (
    <button
      type="button"
      data-chart-item=""
      aria-pressed={selected}
      aria-label={describe(mark)}
      onClick={onSelect}
      className={`pointer-events-auto relative inline-flex items-baseline gap-[0.12em] rounded-[0.3em] px-[0.28em] leading-[1.35] font-medium whitespace-nowrap transition-shadow duration-200 ${tint} ${
        selected ? "shadow-[0_0_0_1.5px_var(--pen)]" : "hover:shadow-[0_0_0_1px_var(--rule-strong)]"
      }`}
    >
      {mark.abbr}
      {mark.retrograde && !NODES.has(mark.name) && <span className="font-mono text-[0.72em] text-blue">R</span>}
      {mark.combust && <span className="font-mono text-[0.72em] text-amber">C</span>}
      {mark.doubt && <span className="pen text-[1.1em] leading-none">?</span>}
    </button>
  );
}

/** The Lagna, written in pen like a marker's note. */
export function LagnaLabel({ state, selected, onSelect }: { state: Exclude<LagnaMark, null>; selected: boolean; onSelect: () => void }) {
  const label =
    state === "sure" ? "Lagna" : state === "likely" ? "Lagna, but a small error in the birth time would move it" : "Possible Lagna";
  return (
    <button
      type="button"
      data-chart-item=""
      aria-pressed={selected}
      aria-label={label}
      onClick={onSelect}
      className={`pen pointer-events-auto inline-flex items-baseline gap-[0.2em] rounded-[0.3em] px-[0.28em] text-[1.08em] leading-[1.3] whitespace-nowrap transition-shadow duration-200 ${
        state === "possible" ? "opacity-60" : ""
      } ${selected ? "shadow-[0_0_0_1.5px_var(--pen)]" : "hover:shadow-[0_0_0_1px_var(--rule-strong)]"}`}
    >
      La{state !== "sure" && "?"}
    </button>
  );
}
