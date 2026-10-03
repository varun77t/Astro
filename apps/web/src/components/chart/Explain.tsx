import { cellInHouse, type Kundli, ordinal, SIGN_LORD } from "@/lib/kundli";
import type { Chart, GlossaryEntry } from "@/lib/types";
import type { Selection } from "./ChartMarks";

type Row = { id: string; note?: string; full?: boolean };

type Explanation = { title: string; facts: string | null; rows: Row[] };

const NODES = new Set(["Rahu", "Ketu"]);
const STRONG = new Set(["exalted", "moolatrikona", "own", "debilitated"]);

/** What to say about the current selection: a title, the numbers, and which glossary entries explain it. */
export function explain(chart: Chart, k: Kundli, s: Exclude<Selection, null>): Explanation {
  const r = chart.reliability;
  const d9 = k.varga === "D9";
  const fromMoon = k.basis === "moon" ? " from the Moon" : "";

  if (s.kind === "planet") {
    const p = chart.planets.find((q) => q.name === s.name)!;
    const cell = k.cells.find((c) => c.planets.some((m) => m.name === s.name))!;
    const mark = cell.planets.find((m) => m.name === s.name)!;
    const rows: Row[] = [];
    if (d9) rows.push({ id: "concept.navamsa" });
    rows.push({ id: `planet.${p.name.toLowerCase()}`, full: true }, { id: `sign.${cell.sign.toLowerCase()}` }, { id: `house.${cell.house}` });
    if (!d9 && p.dignity) rows.push({ id: `dignity.${p.dignity}` });
    if (!d9 && p.retrograde && !NODES.has(p.name)) rows.push({ id: "state.retrograde" });
    if (!d9 && p.combust) rows.push({ id: "state.combust" });
    if (mark.doubt === "boundary") rows.push({ id: "concept.sign_boundary" });
    if (mark.doubt === "window") {
      const signs = d9 ? r.navamsa_moon_signs : r.moon_signs;
      rows.push({
        id: "concept.rashi",
        note: `The Moon moved ${d9 ? "navamsa" : "sign"} within your birth-time window (${signs.join(" to ")}), so this placement is uncertain.`,
      });
    }
    return {
      title: d9 ? `${p.name} in ${cell.sign} navamsa, ${ordinal(cell.house)} house${fromMoon}` : `${p.name} in ${cell.sign}, ${ordinal(cell.house)} house${fromMoon}`,
      facts: d9 ? null : `${p.nakshatra} nakshatra${p.dignity && STRONG.has(p.dignity) ? ` · ${p.dignity}` : ""}`,
      rows,
    };
  }

  if (s.kind === "lagna") {
    const cell = cellInHouse(k, 1);
    const rows: Row[] = [{ id: "concept.lagna", full: true }, { id: `sign.${cell.sign.toLowerCase()}` }];
    if (d9) rows.unshift({ id: "concept.navamsa" });
    if (cell.lagna === "likely") {
      const others = (d9 ? r.navamsa_ascendant_signs : r.ascendant_signs).filter((x) => x !== cell.sign);
      rows.push({ id: "concept.sign_boundary", note: `A few minutes' error in the birth time would make it ${others.join(" or ")}.` });
    }
    return {
      title: `${d9 ? "Navamsa Lagna" : "Lagna"} in ${cell.sign}`,
      facts: d9 ? null : `${chart.ascendant.nakshatra} nakshatra`,
      rows,
    };
  }

  const cell = k.cells.find((c) => c.sign === s.sign)!;
  const lord = SIGN_LORD[cell.sign];
  const lordCell = k.cells.find((c) => c.planets.some((m) => m.name === lord))!;
  const rows: Row[] = [{ id: `house.${cell.house}`, full: true }, { id: `sign.${cell.sign.toLowerCase()}` }];
  if (k.basis === "moon") rows.push({ id: "concept.chandra_lagna" });
  if (cell.lagna === "possible") rows.push({ id: "concept.lagna", note: "Your Lagna may be in this sign; the birth time can't settle which." });
  const holds = cell.planets.map((m) => m.name).join(", ");
  return {
    title: `${ordinal(cell.house)} house${fromMoon}: ${cell.sign}`,
    facts: `Lord ${lord}, in the ${ordinal(lordCell.house)} house · ${holds ? `holds ${holds}` : "no planets here"}`,
    rows,
  };
}

type Props = {
  chart: Chart;
  kundli: Kundli;
  selection: Selection;
  glossary: Map<string, GlossaryEntry> | null;
  glossaryFailed: boolean;
  onRetry: () => void;
};

/** The marker's explanation of whatever was tapped, one ruled line per term. */
export function Explain({ chart, kundli, selection, glossary, glossaryFailed, onRetry }: Props) {
  if (!selection) {
    return (
      <p className="pen text-lg leading-[var(--line)] text-pen">Tap a planet or a house.</p>
    );
  }

  const { title, facts, rows } = explain(chart, kundli, selection);
  return (
    <div>
      <p data-explain-row="" className="leading-[var(--line)] font-medium text-ink">
        <span className="pen mr-3 text-lg font-normal text-pen">Note</span>
        {title}
      </p>
      {facts && (
        <p data-explain-row="" className="text-sm leading-[var(--line)] text-muted">
          {facts}
        </p>
      )}
      <dl className="mt-3 max-w-[46ch] space-y-3">
        {rows.map((row) => {
          const entry = glossary?.get(row.id);
          return (
            <div key={row.id} data-explain-row="" className="">
              <dt className="text-sm text-muted">
                {entry ? (
                  <>
                    {entry.term}{" "}
                    <span lang="sa" className="font-deva text-[0.9em]">
                      {entry.sanskrit}
                    </span>
                  </>
                ) : (
                  row.id.split(".")[1].replace("_", " ")
                )}
              </dt>
              <dd className="leading-relaxed text-ink-2">
                {row.note ?? (entry ? (row.full ? `${entry.short} ${entry.body}` : entry.short) : null)}
              </dd>
            </div>
          );
        })}
      </dl>
      {glossaryFailed && (
        <p className="mt-2 text-sm text-muted">
          The explanations didn&apos;t load.{" "}
          <button type="button" onClick={onRetry} className="link">
            Try again
          </button>
        </p>
      )}
    </div>
  );
}
