"use client";

import { ChartFigure } from "@/components/chart/ChartFigure";
import { DashaTimeline } from "@/components/chart/DashaTimeline";
import { PlanetTable } from "@/components/chart/PlanetTable";
import { PenNote, Term, Tick } from "@/components/paper/Marks";
import { Readings } from "@/components/reading/Readings";
import { createChart, createDasha, createReadings } from "@/lib/api";
import { formatDegree } from "@/lib/format";
import type { BirthInput, Chart, Dasha, Readings as ReadingsData } from "@/lib/types";

/** Everything the chart page shows for one birth. */
export type Answer = { birth: BirthInput; chart: Chart; dasha: Dasha | null; readings: ReadingsData | null };

/** Readings and periods are extras: if they fail, the chart still shows. */
export async function loadAnswer(birth: BirthInput): Promise<Answer> {
  const [chart, dasha, readings] = await Promise.allSettled([createChart(birth), createDasha(birth), createReadings(birth)]);
  if (chart.status === "rejected") throw chart.reason;
  return {
    birth,
    chart: chart.value,
    dasha: dasha.status === "fulfilled" ? dasha.value : null,
    readings: readings.status === "fulfilled" ? readings.value : null,
  };
}

/** A chart with everything read from it: the drawing fills the right column; title, summary and
 * explanations sit beside it; readings and periods follow below. `actions` goes under the summary. */
export function ChartAnswer({
  answer: { chart, dasha, readings, birth },
  header,
  actions,
}: {
  answer: Answer;
  header: React.ReactNode;
  actions: React.ReactNode;
}) {
  const { reliability: r, ascendant: asc } = chart;
  const lagnaKnown = r.time_accuracy !== "unknown" && r.basis === "ascendant";
  const moon = chart.planets.find((p) => p.name === "Moon")!;
  const onEdge = chart.planets.filter((p) => p.degree_in_sign < 1 / 60 || 30 - p.degree_in_sign < 1 / 60);

  return (
    <>
      <ChartFigure
        chart={chart}
        intro={header}
        aside={
          <div className="space-y-6">
            <dl style={{ lineHeight: "var(--line)" }}>
              <Summary term={<Term en="Lagna" deva="लग्न" />} sure={lagnaKnown && r.ascendant_reliable}>
                {lagnaKnown ? asc.sign : <span className="text-muted">Unknown</span>}
              </Summary>
              <Summary term={<Term en="Moon sign" deva="राशि" />} sure={r.moon_sign_reliable}>
                {r.moon_sign_reliable ? moon.sign : r.moon_signs.join(" or ")}
              </Summary>
              <Summary term={<Term en="Nakshatra" deva="नक्षत्र" />} sure={r.moon_nakshatra_reliable}>
                {r.moon_nakshatra_reliable ? moon.nakshatra : r.moon_nakshatras.join(" or ")}
              </Summary>
            </dl>

            {r.warnings.map((w) => (
              <PenNote key={w}>{w}</PenNote>
            ))}
            {onEdge.map((p) => (
              <PenNote key={p.name} label="Edge">
                {p.name} sits right on a sign boundary, so its sign is marked ?.
              </PenNote>
            ))}

            {actions}
          </div>
        }
        below={
          <details className="group border-t border-rule-strong/70">
            <summary className="flex cursor-pointer list-none items-center justify-between py-4 text-ink [&::-webkit-details-marker]:hidden">
              All positions
              <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden>
                <path d="M1 7h12" stroke="currentColor" strokeWidth="1.6" />
                <path
                  d="M7 1v12"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  className="origin-center transition-transform duration-300 group-open:scale-y-0"
                />
              </svg>
            </summary>
            <PlanetTable planets={chart.planets} fromMoon={r.basis === "moon"} />
            <p className="mt-3 text-xs text-muted">
              Sidereal, Lahiri ayanamsa {formatDegree(chart.meta.ayanamsa_value)}, whole-sign houses.
            </p>
          </details>
        }
      />
      {readings && <Readings data={readings} birth={birth} />}
      {dasha && <DashaTimeline dasha={dasha} birthUtc={chart.meta.utc} />}
    </>
  );
}

/** A line of the answer. A tick when the birth time supports it; a "?" in pen when it doesn't. */
function Summary({ term, sure, children }: { term: React.ReactNode; sure?: boolean; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[minmax(0,9.5rem)_1fr] gap-4">
      <dt className="text-sm leading-[var(--line)] text-muted">{term}</dt>
      <dd className="text-ink">
        {children}
        {sure === true && <Tick data-mark="" className="ml-2" />}
        {sure === false && <span className="pen ml-2 text-lg">?</span>}
      </dd>
    </div>
  );
}
