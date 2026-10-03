"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChoiceTabs } from "@/components/paper/ChoiceTabs";
import { loadGlossary } from "@/lib/api";
import { buildKundli, type Varga } from "@/lib/kundli";
import { EASE_OUT, gsap, MOTION_OK, useGSAP } from "@/lib/motion";
import type { Chart, GlossaryEntry } from "@/lib/types";
import type { Selection } from "./ChartMarks";
import { Explain } from "./Explain";
import { NorthIndianChart } from "./NorthIndianChart";
import { SouthIndianChart } from "./SouthIndianChart";

type Style = "south" | "north";
const STYLE_KEY = "vedic-astro.chart-style";

function readStyle(): Style {
  try {
    return localStorage.getItem(STYLE_KEY) === "north" ? "north" : "south";
  } catch {
    return "south";
  }
}

type Props = {
  chart: Chart;
  /** Title block: top left on a wide screen, first on a phone. */
  intro: React.ReactNode;
  /** The summary: beside the chart on a wide screen, after the explanation on a phone. */
  aside: React.ReactNode;
  /** Under the chart. */
  below: React.ReactNode;
};

/**
 * The chart step's layout. Wide screens: the drawing fills the right column at a size that fits the
 * window, and the left column holds the title, the summary and the explanation of whatever is
 * tapped, so nothing needs a scroll. Phones: title, chart, explanation, summary, then the rest.
 */
export function ChartFigure({ chart, intro, aside, below }: Props) {
  const [style, setStyle] = useState<Style>("south");
  const [varga, setVarga] = useState<Varga>("D1");
  const [selection, setSelection] = useState<Selection>(null);
  const [glossary, setGlossary] = useState<Map<string, GlossaryEntry> | null>(null);
  const [glossaryFailed, setGlossaryFailed] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const explainRef = useRef<HTMLDivElement>(null);

  // localStorage only exists in the browser, so read the remembered style after mount.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setStyle(readStyle()), []);

  const fetchGlossary = () => loadGlossary().then(setGlossary, () => setGlossaryFailed(true));
  useEffect(() => {
    fetchGlossary();
  }, []);
  const retryGlossary = () => {
    setGlossaryFailed(false);
    fetchGlossary();
  };

  const kundli = useMemo(() => buildKundli(chart, varga), [chart, varga]);
  // A Lagna selection means nothing in a chart drawn from the Moon.
  const shown: Selection = selection?.kind === "lagna" && kundli.basis !== "lagna" ? null : selection;

  function changeStyle(next: Style) {
    setStyle(next);
    try {
      localStorage.setItem(STYLE_KEY, next);
    } catch {
      // Private mode or blocked storage: the choice just isn't remembered.
    }
  }

  function changeVarga(next: Varga) {
    setVarga(next);
    // A house selection is a sign, which means something different in the other chart.
    setSelection((s) => (s?.kind === "house" ? null : s));
  }

  function select(next: Selection) {
    const same = JSON.stringify(next) === JSON.stringify(shown);
    setSelection(same ? null : next);
    if (!same) {
      // On a phone the explanation sits below the fold; bring it up without jumping when it's already visible.
      requestAnimationFrame(() => {
        const el = explainRef.current;
        if (!el) return;
        const { top, bottom } = el.getBoundingClientRect();
        if (top > window.innerHeight - 80 || bottom < 0) el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
    }
  }

  // Draw the frame, then write the planets in. Re-runs when the chart changes shape.
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION_OK, () => {
        gsap
          .timeline()
          .fromTo("[data-chart-line]", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut", stagger: 0.05 })
          .fromTo("[data-chart-pen]", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.35, ease: "power2.out" }, "-=0.2")
          .fromTo("[data-chart-item]", { autoAlpha: 0, y: 4 }, { autoAlpha: 1, y: 0, duration: 0.6, ease: EASE_OUT, stagger: 0.025 }, "-=0.35");
      });
      return () => mm.revert();
    },
    { scope: root, dependencies: [style, varga], revertOnUpdate: true },
  );

  useGSAP(
    () => {
      if (!shown) return;
      const mm = gsap.matchMedia();
      mm.add(MOTION_OK, () => {
        gsap.fromTo("[data-explain-row]", { autoAlpha: 0, x: -8 }, { autoAlpha: 1, x: 0, duration: 0.5, ease: EASE_OUT, stagger: 0.04 });
      });
      return () => mm.revert();
    },
    { scope: explainRef, dependencies: [shown, varga, glossary], revertOnUpdate: true },
  );

  const Drawing = style === "south" ? SouthIndianChart : NorthIndianChart;
  return (
    <div ref={root} className="grid gap-x-12 gap-y-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:grid-rows-[auto_auto_1fr_auto]">
      <div className="lg:col-start-1 lg:row-start-1">{intro}</div>

      <div className="lg:col-start-2 lg:row-span-3 lg:row-start-1">
        <div className="mb-4 flex flex-wrap gap-x-10 gap-y-1">
          <ChoiceTabs
            legend="Style"
            name="chart-style"
            value={style}
            onChange={changeStyle}
            options={[
              { value: "south", label: "South Indian" },
              { value: "north", label: "North Indian" },
            ]}
          />
          <ChoiceTabs
            legend="Chart"
            name="chart-varga"
            value={varga}
            onChange={changeVarga}
            options={[
              { value: "D1", label: "Rashi D1" },
              { value: "D9", label: "Navamsa D9" },
            ]}
          />
        </div>

        {/* On a wide screen the square is capped by the window height, so it arrives whole. */}
        <figure className="max-w-[34rem] lg:max-w-[min(34rem,calc(100svh-12rem))]">
          <Drawing kundli={kundli} selection={shown} onSelect={select} />
          <figcaption className="mt-3 flex flex-wrap gap-x-4 text-xs text-muted">
            {kundli.basis === "moon" && <span>Houses counted from the Moon.</span>}
            {style === "north" && <span>Numbers are signs, 1 = Aries.</span>}
            <span>
              <span className="pen text-sm text-pen">La</span> Lagna
            </span>
            <span>
              <span className="font-mono text-blue">R</span> retrograde
            </span>
            <span>
              <span className="font-mono text-amber">C</span> combust
            </span>
            <span>
              <span className="pen text-sm text-pen">?</span> uncertain
            </span>
          </figcaption>
        </figure>
      </div>

      <div ref={explainRef} aria-live="polite" className="lg:col-start-1 lg:row-start-3">
        <Explain chart={chart} kundli={kundli} selection={shown} glossary={glossary} glossaryFailed={glossaryFailed} onRetry={retryGlossary} />
      </div>

      <div className="lg:col-start-1 lg:row-start-2">{aside}</div>

      <div className="lg:col-start-2 lg:row-start-4">{below}</div>
    </div>
  );
}
