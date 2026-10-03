"use client";

import { useRef, useState } from "react";
import { PlanetTable } from "@/components/chart/PlanetTable";
import { ChartFigure } from "@/components/chart/ChartFigure";
import { DashaTimeline } from "@/components/chart/DashaTimeline";
import { Readings } from "@/components/reading/Readings";
import { BirthForm } from "@/components/forms/BirthForm";
import { ConfirmBirth, type ConfirmedOptions } from "@/components/forms/ConfirmBirth";
import { PenNote, Term, Tick } from "@/components/paper/Marks";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { createChart, createDasha, createReadings } from "@/lib/api";
import { type BirthFormState, emptyBirthForm, toBirthInput } from "@/lib/birth";
import { formatDegree } from "@/lib/format";
import { EASE_OUT, gsap, MOTION_OK, useGSAP } from "@/lib/motion";
import type { BirthInput, Chart, Dasha, Readings as ReadingsData } from "@/lib/types";

type Step = "form" | "confirm" | "chart";

const STEPS: { key: Step; label: string; title: string; lede: string }[] = [
  {
    key: "form",
    label: "Details",
    title: "Your birth details.",
    lede: "Three questions.",
  },
  {
    key: "confirm",
    label: "Check",
    title: "Is this right?",
    lede: "A wrong time zone shifts the whole chart.",
  },
  {
    key: "chart",
    label: "Chart",
    title: "Your chart.",
    lede: "",
  },
];

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>("form");
  const [form, setForm] = useState<BirthFormState>(emptyBirthForm);
  const [chart, setChart] = useState<Chart | null>(null);
  const [dasha, setDasha] = useState<Dasha | null>(null);
  // The readings, with the birth input they came from (each area's written reading is fetched later).
  const [readings, setReadings] = useState<{ data: ReadingsData; birth: BirthInput } | null>(null);
  const [busy, setBusy] = useState(false);
  const [chartError, setChartError] = useState("");
  const root = useRef<HTMLElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);

  // Each new page of the paper settles in; the chart's rows are written in one by one.
  useGSAP(
    () => {
      gsap.matchMedia().add(MOTION_OK, () => {
        gsap.from("[data-step-in]", {
          y: 14,
          autoAlpha: 0,
          duration: 0.8,
          ease: EASE_OUT,
          stagger: 0.06,
        });
        gsap.from("[data-row]", {
          autoAlpha: 0,
          x: -8,
          duration: 0.5,
          ease: EASE_OUT,
          stagger: 0.06,
          delay: 0.25,
        });
        gsap.fromTo(
          "[data-mark] path",
          { strokeDashoffset: 1 },
          {
            strokeDashoffset: 0,
            duration: 0.5,
            delay: 0.6,
            ease: "power2.out",
          },
        );
      });
    },
    { scope: root, dependencies: [step] },
  );

  function go(next: Step) {
    setStep(next);
    window.scrollTo({ top: 0 });
    setTimeout(() => headingRef.current?.focus(), 0);
  }

  async function confirm(options: ConfirmedOptions) {
    setBusy(true);
    setChartError("");
    try {
      const input = toBirthInput(form, options);
      // Readings and periods are extras on the chart page: if they fail, the chart still shows.
      const [chartResult, dashaResult, readingsResult] = await Promise.allSettled([
        createChart(input),
        createDasha(input),
        createReadings(input),
      ]);
      if (chartResult.status === "rejected") throw chartResult.reason;
      setChart(chartResult.value);
      setDasha(dashaResult.status === "fulfilled" ? dashaResult.value : null);
      setReadings(readingsResult.status === "fulfilled" ? { data: readingsResult.value, birth: input } : null);
      go("chart");
    } catch (err) {
      setChartError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const current = STEPS.find((s) => s.key === step)!;

  const header = (
    <>
      <ol aria-label="Progress" className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
        {STEPS.map((s, i) => {
          const done = STEPS.findIndex((x) => x.key === step) > i;
          const now = s.key === step;
          return (
            <li key={s.key} aria-current={now ? "step" : undefined} className={now ? "text-ink" : "text-muted"}>
              <span className="font-mono text-xs">{i + 1}</span>{" "}
              <span className={now ? "underline decoration-pen decoration-2 underline-offset-[6px]" : ""}>{s.label}</span>
              {done && <span className="sr-only"> (done)</span>}
            </li>
          );
        })}
      </ol>

      <h1
        ref={headingRef}
        tabIndex={-1}
        data-step-in
        className={`serif outline-none ${step === "chart" ? "mt-5 text-[clamp(2.2rem,4vw,3rem)]" : "mt-7 text-[clamp(2.8rem,6vw,4.4rem)]"}`}
      >
        {current.title}
      </h1>
      {current.lede && (
        <p data-step-in className="mt-4 max-w-[52ch] text-lg">
          {current.lede}
        </p>
      )}
    </>
  );

  return (
    <Sheet>
      <main ref={root} className={`${SHEET_X} pt-8 pb-24 sm:pt-10`}>
        {step === "chart" && chart ? (
          <ChartAnswer
            chart={chart}
            dasha={dasha}
            readings={readings}
            header={header}
            onRestart={() => {
              setChart(null);
              setDasha(null);
              setReadings(null);
              setForm(emptyBirthForm);
              go("form");
            }}
          />
        ) : (
          <div className="max-w-3xl">
            {header}
            <div data-step-in className="mt-10">
              {step === "form" && (
                <BirthForm
                  initial={form}
                  onSubmit={(f) => {
                    setForm(f);
                    go("confirm");
                  }}
                />
              )}
              {step === "confirm" && (
                <ConfirmBirth form={form} busy={busy} error={chartError} onBack={() => go("form")} onConfirm={confirm} />
              )}
            </div>
          </div>
        )}
      </main>
    </Sheet>
  );
}

/** The chart step: the drawing fills the right column; title, summary and explanations sit beside it. */
function ChartAnswer({
  chart,
  dasha,
  readings,
  header,
  onRestart,
}: {
  chart: Chart;
  dasha: Dasha | null;
  readings: { data: ReadingsData; birth: BirthInput } | null;
  header: React.ReactNode;
  onRestart: () => void;
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

            <button type="button" onClick={onRestart} className="link">
              Start a new chart
            </button>
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
      {readings && <Readings data={readings.data} birth={readings.birth} />}
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
