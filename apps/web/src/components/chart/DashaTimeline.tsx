"use client";

import { useEffect, useRef, useState } from "react";
import { PenNote, Term, Tick } from "@/components/paper/Marks";
import { loadGlossary } from "@/lib/api";
import { describeUncertainty, lifeLine, monthYear, yearOf } from "@/lib/dasha";
import { PLANET_ABBR } from "@/lib/kundli";
import { EASE_OUT, gsap, MOTION_OK, useGSAP } from "@/lib/motion";
import type { Dasha, GlossaryEntry } from "@/lib/types";

/** Vimshottari periods: what's running now, the life laid out as a number line, and the sub-periods of one. */
export function DashaTimeline({ dasha, birthUtc }: { dasha: Dasha; birthUtc: string }) {
  const { segments, now } = lifeLine(dasha, birthUtc);
  const current = dasha.current;
  const [picked, setPicked] = useState(current?.mahadasha.lord ?? dasha.mahadashas[0].lord);
  const [glossary, setGlossary] = useState<Map<string, GlossaryEntry> | null>(null);
  const root = useRef<HTMLElement>(null);
  const list = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadGlossary().then(setGlossary, () => {});
  }, []);

  const md = dasha.mahadashas.find((m) => m.lord === picked)!;
  const asOf = Date.parse(dasha.as_of);
  const uncertainty = describeUncertainty(dasha.uncertainty_days);

  // The line is ruled when the section arrives; the sub-periods are written in whenever they change.
  useGSAP(
    () => {
      gsap.matchMedia().add(MOTION_OK, () => {
        gsap
          .timeline({ scrollTrigger: { trigger: root.current, start: "top 75%", once: true } })
          .from("[data-dasha-rule]", { scaleX: 0, transformOrigin: "left center", duration: 0.9, ease: "power2.inOut" })
          .from("[data-dasha-mark]", { autoAlpha: 0, y: 4, duration: 0.5, ease: EASE_OUT, stagger: 0.04 }, "-=0.5");
      });
    },
    { scope: root },
  );
  useGSAP(
    () => {
      gsap.matchMedia().add(MOTION_OK, () => {
        gsap.from("[data-dasha-row]", { autoAlpha: 0, x: -8, duration: 0.45, ease: EASE_OUT, stagger: 0.035 });
      });
    },
    { scope: list, dependencies: [picked], revertOnUpdate: true },
  );

  return (
    <section
      ref={root}
      className="mt-24 grid gap-x-12 gap-y-10 border-t border-rule-strong/70 pt-14 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]"
    >
      <div className="space-y-4">
        <h2 className="serif text-[clamp(2.2rem,4vw,3rem)]">Your periods.</h2>
        <p className="max-w-[40ch] text-ink-2">
          In <Term en="Vimshottari dasha" deva="विंशोत्तरी दशा" />, life runs through nine planetary periods, each split into sub-periods.
        </p>
      </div>

      <div className="space-y-4 lg:pt-3">
        {current && (
          <dl style={{ lineHeight: "var(--line)" }}>
            <div className="grid grid-cols-[8rem_1fr]">
              <dt className="text-sm leading-[var(--line)] text-muted">Period now</dt>
              <dd className="text-ink">
                {current.mahadasha.lord} <span className="text-muted">until {monthYear(current.mahadasha.end)}</span>
              </dd>
            </div>
            <div className="grid grid-cols-[8rem_1fr]">
              <dt className="text-sm leading-[var(--line)] text-muted">Sub-period</dt>
              <dd className="text-ink">
                {current.antardasha.lord} <span className="text-muted">until {monthYear(current.antardasha.end)}</span>
              </dd>
            </div>
          </dl>
        )}

        {!dasha.timing_reliable ? (
          <PenNote>The birth time is too loose to fix where the periods start, so treat these dates as a rough guide.</PenNote>
        ) : (
          uncertainty && <PenNote>Because the birth time is approximate, these dates could be off by {uncertainty}.</PenNote>
        )}
      </div>

      {/* The life as a number line across the page: one stretch per planet, years at the ticks. */}
      <div className="lg:col-span-2">
        <div className="relative h-[5.75rem] select-none" role="group" aria-label="Periods across your life">
          <span data-dasha-rule aria-hidden className="absolute top-8 right-0 left-0 h-px bg-ink-2" />
          {segments.map((s, i) => {
            const narrow = s.width < 6.5;
            const selected = s.lord === picked;
            return (
              <button
                key={s.lord}
                type="button"
                aria-pressed={selected}
                aria-label={`${s.lord} period, ${monthYear(s.start)} to ${monthYear(s.end)}${s.isCurrent ? ", running now" : ""}`}
                onClick={() => setPicked(s.lord)}
                style={{ left: `${s.left}%`, width: `${s.width}%` }}
                className="group absolute top-0 h-12"
              >
                <span
                  data-dasha-mark
                  className={`absolute inset-x-0 top-0 truncate text-center text-sm leading-6 transition-colors duration-200 ${
                    selected ? "text-ink" : "text-muted group-hover:text-ink"
                  }`}
                >
                  {narrow ? PLANET_ABBR[s.lord] : s.lord}
                </span>
                {selected && <span aria-hidden className="absolute inset-x-0 top-[calc(2rem-1px)] h-[3px] bg-pen" />}
                {/* Tick and year at the start; the very first one is the birth year. */}
                <span aria-hidden className="absolute top-[1.625rem] left-0 h-3 w-px bg-ink-2" />
                <span data-dasha-mark aria-hidden className="absolute top-11 left-0 -translate-x-1/2 font-mono text-[0.68rem] text-muted">
                  {i === 0 ? yearOf(birthUtc) : yearOf(s.start)}
                </span>
              </button>
            );
          })}
          <span aria-hidden className="absolute top-[1.625rem] right-0 h-3 w-px bg-ink-2" />
          <span data-dasha-mark aria-hidden className="absolute top-11 right-0 translate-x-1/2 font-mono text-[0.68rem] text-muted">
            {yearOf(segments[segments.length - 1].end)}
          </span>
          {now !== null && (
            <span data-dasha-mark aria-hidden className="pointer-events-none absolute top-6 bottom-0" style={{ left: `${now}%` }}>
              <span className="absolute top-0 h-5 w-[2px] -translate-x-1/2 bg-pen" />
              <span className="pen absolute top-[3.1rem] -translate-x-1/2 text-base leading-none">now</span>
            </span>
          )}
        </div>
      </div>

      <div>
        <p className="text-ink">
          {md.lord} period{" "}
          <span className="text-muted">
            {monthYear(md.start)} to {monthYear(md.end)}
          </span>
        </p>
        {glossary?.get(`planet.${md.lord.toLowerCase()}`) && (
          <p className="mt-1 max-w-[40ch] text-ink-2">{glossary.get(`planet.${md.lord.toLowerCase()}`)!.short}</p>
        )}
        <p className="pen mt-4 text-base text-pen">Tap another period on the line.</p>
      </div>

      <div ref={list}>
        <ol>
          {md.antardashas.map((ad) => {
            const running = Date.parse(ad.start) <= asOf && asOf < Date.parse(ad.end);
            const past = Date.parse(ad.end) <= asOf;
            return (
              <li
                key={ad.lord}
                data-dasha-row
                aria-current={running ? "true" : undefined}
                className={`grid h-[var(--line)] grid-cols-[7rem_14rem_auto] items-baseline leading-[var(--line)] ${past ? "text-muted" : "text-ink"}`}
              >
                <span className={running ? "font-medium" : ""}>{ad.lord}</span>
                <span className={`font-mono text-[0.8rem] ${past ? "" : "text-ink-2"}`}>
                  {monthYear(ad.start)} – {monthYear(ad.end)}
                </span>
                <span>
                  {running && (
                    <>
                      <span className="pen text-base">now</span>
                      <Tick className="ml-1" />
                    </>
                  )}
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
