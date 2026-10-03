import { cellInHouse, type Kundli, NORTH_HOUSES, ordinal, SIGNS } from "@/lib/kundli";
import { LagnaLabel, PlanetLabel, type Selection } from "./ChartMarks";

// The frame, both diagonals, and the diamond through the edge midpoints.
const LINES = ["M0 0H400V400H0Z", "M0 0L400 400", "M400 0L0 400", "M200 0L400 200L200 400L0 200Z"];

// How wide a house's planet block may grow, as a share of the chart. Side triangles are narrow.
const BLOCK_WIDTH: Record<number, string> = { 1: "34%", 4: "30%", 7: "34%", 10: "30%", 2: "30%", 6: "30%", 8: "30%", 12: "30%", 3: "15%", 5: "15%", 9: "15%", 11: "15%" };

type Props = {
  kundli: Kundli;
  selection: Selection;
  onSelect: (s: Selection) => void;
};

const pct = ([x, y]: [number, number]) => ({ left: `${x}%`, top: `${y}%` });

/** North Indian chart: the houses are fixed, the 1st at the top, counted anticlockwise; sign numbers rotate with the 1st house. */
export function NorthIndianChart({ kundli, selection, onSelect }: Props) {
  return (
    <div className="@container relative aspect-square w-full bg-bone text-[clamp(0.66rem,3.2cqw,0.92rem)]">
      <svg viewBox="0 0 400 400" preserveAspectRatio="none" aria-hidden className="absolute inset-0 h-full w-full overflow-visible">
        {Object.entries(NORTH_HOUSES).map(([n, h]) => {
          const cell = cellInHouse(kundli, Number(n));
          const selected = selection?.kind === "house" && selection.sign === cell.sign;
          return (
            <polygon
              key={n}
              points={h.shape.map(([x, y]) => `${x * 4},${y * 4}`).join(" ")}
              onClick={() => onSelect({ kind: "house", sign: cell.sign })}
              className={`cursor-pointer transition-colors duration-200 ${selected ? "fill-paper" : "fill-transparent hover:fill-paper/60"}`}
            />
          );
        })}
        {LINES.map((d) => (
          <path
            key={d}
            d={d}
            data-chart-line=""
            fill="none"
            stroke="var(--ink-2)"
            strokeWidth={1.5}
            strokeLinejoin="round"
            pathLength={1}
            strokeDasharray={1}
            className="pointer-events-none"
          />
        ))}
      </svg>

      {Object.entries(NORTH_HOUSES).map(([n, h]) => {
        const house = Number(n);
        const cell = cellInHouse(kundli, house);
        const selected = selection?.kind === "house" && selection.sign === cell.sign;
        const occupants = cell.planets.map((p) => p.name).join(", ") || "empty";
        return (
          <div key={n} role="group" aria-label={`${ordinal(house)} house, ${cell.sign}: ${occupants}`} className="contents">
            <button
              type="button"
              aria-pressed={selected}
              aria-label={`${ordinal(house)} house, ${cell.sign}`}
              title={cell.sign}
              onClick={() => onSelect({ kind: "house", sign: cell.sign })}
              style={pct(h.sign)}
              className={`absolute -translate-x-1/2 -translate-y-1/2 rounded-[0.3em] px-[0.3em] font-mono text-[0.78em] leading-tight ${
                selected ? "text-pen" : "text-muted hover:text-ink"
              }`}
            >
              {SIGNS.indexOf(cell.sign as (typeof SIGNS)[number]) + 1}
            </button>
            <div
              style={{ ...pct(h.planets), width: BLOCK_WIDTH[house] }}
              className="pointer-events-none absolute flex -translate-x-1/2 -translate-y-1/2 flex-wrap content-center items-center justify-center gap-x-[0.8cqw] gap-y-[0.3cqw]"
            >
              {cell.lagna && (
                <LagnaLabel
                  state={cell.lagna}
                  selected={selection?.kind === "lagna" && cell.lagna !== "possible"}
                  onSelect={() => onSelect(cell.lagna === "possible" ? { kind: "house", sign: cell.sign } : { kind: "lagna" })}
                />
              )}
              {cell.planets.map((mark) => (
                <PlanetLabel
                  key={mark.name}
                  mark={mark}
                  selected={selection?.kind === "planet" && selection.name === mark.name}
                  onSelect={() => onSelect({ kind: "planet", name: mark.name })}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
