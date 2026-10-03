import { type ChartCell, type Kundli, ordinal, SIGN_ABBR, SOUTH_GRID } from "@/lib/kundli";
import { LagnaLabel, PlanetLabel, type Selection } from "./ChartMarks";
import { Term } from "@/components/paper/Marks";

// Ruled in a 4×4 square: the outer frame, then the inner rules that skip the centre.
const LINES = [
  "M0 0H400V400H0Z",
  "M0 100H400",
  "M0 300H400",
  "M100 0V400",
  "M300 0V400",
  "M0 200H100",
  "M300 200H400",
  "M200 0V100",
  "M200 300V400",
];

const VARGA_NAME = {
  D1: { en: "Rashi", deva: "राशि" },
  D9: { en: "Navamsa", deva: "नवांश" },
};

type Props = {
  kundli: Kundli;
  selection: Selection;
  onSelect: (s: Selection) => void;
};

/** South Indian chart: the twelve signs sit in fixed boxes round the edge, Pisces top left, running clockwise. */
export function SouthIndianChart({ kundli, selection, onSelect }: Props) {
  const name = VARGA_NAME[kundli.varga];
  return (
    <div className="@container relative aspect-square w-full bg-bone text-[clamp(0.68rem,3.4cqw,0.95rem)]">
      <svg viewBox="0 0 400 400" preserveAspectRatio="none" aria-hidden className="absolute inset-0 h-full w-full overflow-visible">
        {LINES.map((d) => (
          <path
            key={d}
            d={d}
            data-chart-line=""
            fill="none"
            stroke="var(--ink-2)"
            strokeWidth={1.25}

            strokeLinecap="square"
            pathLength={1}
            strokeDasharray={1}
          />
        ))}
      </svg>

      <div className="absolute inset-0 grid grid-cols-4 grid-rows-4">
        {kundli.cells.map((cell) => (
          <SouthCell key={cell.sign} cell={cell} selection={selection} onSelect={onSelect} />
        ))}

        <div
          data-chart-item=""
          className="col-span-2 col-start-2 row-span-2 row-start-2 flex flex-col items-center justify-center gap-[1.5cqw] px-[4cqw] text-center"
        >
          <p className="font-mono text-[0.72em] tracking-[0.06em] text-muted uppercase">{kundli.varga}</p>
          <p className="text-[1.15em] leading-tight text-ink">
            <Term en={name.en} deva={name.deva} />
          </p>
          <p className="text-[0.8em] leading-snug text-muted">
            {kundli.basis === "lagna" ? <>Lagna {kundli.firstSign}</> : <>Counted from the Moon</>}
          </p>
        </div>
      </div>
    </div>
  );
}

function SouthCell({ cell, selection, onSelect }: { cell: ChartCell; selection: Selection } & Pick<Props, "onSelect">) {
  const [row, col] = SOUTH_GRID[cell.sign];
  const houseSelected = selection?.kind === "house" && selection.sign === cell.sign;
  const showLagnaHere = cell.lagna !== null;
  const occupants = cell.planets.map((p) => p.name).join(", ") || "empty";

  return (
    <div
      role="group"
      aria-label={`${cell.sign}, ${ordinal(cell.house)} house: ${occupants}`}
      className="relative"
      style={{ gridRow: row + 1, gridColumn: col + 1 }}
    >
      <button
        type="button"
        aria-pressed={houseSelected}
        aria-label={`${cell.sign}, ${ordinal(cell.house)} house`}
        onClick={() => onSelect({ kind: "house", sign: cell.sign })}
        className={`absolute inset-[1px] transition-colors duration-200 ${houseSelected ? "bg-paper" : "hover:bg-paper/60"}`}
      />

      {showLagnaHere && (
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-hidden
          className="pointer-events-none absolute inset-0 h-full w-full overflow-visible"
        >
          {cell.lagna === "possible" ? (
            <path
              d="M0 26 L26 0"
              data-chart-item=""
              fill="none"
              stroke="var(--pen)"
              strokeWidth={1.6}
              strokeDasharray="3 4"
              opacity={0.6}
            />
          ) : (
            <path
              d="M0 26 L26 0"
              data-chart-pen=""
              fill="none"
              stroke="var(--pen)"
              strokeWidth={1.6}

              strokeLinecap="round"
              pathLength={1}
              strokeDasharray={1}
            />
          )}
        </svg>
      )}

      <div className="pointer-events-none relative flex h-full flex-wrap content-center items-center justify-center gap-x-[1cqw] gap-y-[0.4cqw] px-[1.2cqw] pt-[3.5cqw] pb-[5cqw]">
        {showLagnaHere && (
          <LagnaLabel
            state={cell.lagna!}
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

      <span aria-hidden className="pointer-events-none absolute bottom-[1cqw] left-[1.6cqw] font-mono text-[0.68em] text-muted">
        <span className="@md:hidden">{SIGN_ABBR[cell.sign]}</span>
        <span className="hidden @md:inline">{cell.sign}</span>
      </span>
      <span
        aria-hidden
        className={`pointer-events-none absolute right-[1.6cqw] bottom-[1cqw] font-mono text-[0.68em] ${houseSelected ? "text-pen" : "text-muted"}`}
      >
        {cell.house}
      </span>
    </div>
  );
}
