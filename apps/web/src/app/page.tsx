"use client";

import Link from "next/link";
import { useRef } from "react";
import { SouthIndianChart } from "@/components/chart/SouthIndianChart";
import { Arrow, MarginLabel, Term, Tick } from "@/components/paper/Marks";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { buildKundli } from "@/lib/kundli";
import { EASE_OUT, gsap, MOTION_OK, ScrollTrigger, useGSAP, WRITE_FROM, WRITE_TO } from "@/lib/motion";
import sampleChart from "@/lib/sample-chart.json";
import type { Chart } from "@/lib/types";

// A real chart from the engine: 9 Mar 2002, 07:45 IST, Pune. The reading line is illustrative.
const SAMPLE = buildKundli(sampleChart as unknown as Chart, "D1");
const SPLIT = "grid grid-cols-[minmax(0,1fr)] gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-12";
const noop = () => {};

export default function Home() {
  const root = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      gsap.matchMedia().add(MOTION_OK, () => {
        // The chart is drawn, then one line of it is read and marked.
        gsap
          .timeline({ defaults: { ease: EASE_OUT }, delay: 0.15 })
          .from("[data-hero-q]", { autoAlpha: 0, x: -10, duration: 0.8 })
          .from("[data-hero-line]", { y: 22, autoAlpha: 0, duration: 1.1, stagger: 0.08 }, 0.05)
          .fromTo("[data-chart-line]", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.8, ease: "power2.inOut", stagger: 0.05 }, 0.3)
          .fromTo("[data-chart-pen]", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.35, ease: "power2.out" }, ">-0.2")
          .from("[data-chart-item]", { autoAlpha: 0, y: 4, duration: 0.6, stagger: 0.03 }, "<")
          .fromTo("[data-write]", WRITE_FROM, { ...WRITE_TO, duration: 0.85, ease: "power2.inOut", clearProps: "clipPath" }, ">-0.1")
          .fromTo("[data-hero-tick] path", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.4, ease: "power2.out" }, ">-0.1")
          .from("[data-hero-note]", { autoAlpha: 0, y: 6, duration: 0.7 }, "<");

        // Later answers write themselves in at the reader's own pace.
        gsap.utils.toArray<HTMLElement>("[data-answer]").forEach((answer) => {
          gsap
            .timeline({ scrollTrigger: { trigger: answer, start: "top 80%", end: "bottom 62%", scrub: 0.6 } })
            .fromTo(answer.querySelectorAll("[data-scroll-write]"), WRITE_FROM, { ...WRITE_TO, ease: "none", stagger: 0.45 })
            .fromTo(answer.querySelectorAll("[data-strike]"), { scaleX: 0 }, { scaleX: 1, ease: "none", stagger: 0.2 }, "<0.2")
            .fromTo(answer.querySelectorAll("[data-scroll-tick] path"), { strokeDashoffset: 1 }, { strokeDashoffset: 0, ease: "none", stagger: 0.25 }, "<");
        });

        ScrollTrigger.batch("[data-reveal]", {
          start: "top 86%",
          once: true,
          onEnter: (els) => gsap.from(els, { y: 18, autoAlpha: 0, duration: 0.9, ease: EASE_OUT, stagger: 0.08 }),
        });
      });
    },
    { scope: root },
  );

  return (
    <Sheet
      action={
        <Link href="/onboarding" className="btn !px-4 !py-2 !text-sm">
          Calculate my chart
        </Link>
      }
    >
      <main ref={root} className={SHEET_X}>
        <section className={`relative ${SPLIT} pt-16 pb-20 lg:items-center lg:pt-24 lg:pb-24`}>
          <div className="relative">
            <MarginLabel className="top-3 lg:top-5">
              <span data-hero-q>Q1.</span>
            </MarginLabel>
            <h1 data-hero-line className="serif text-[clamp(3.1rem,6vw,5.3rem)]">
              Show your working.
            </h1>
            <p data-hero-line className="mt-6 max-w-[30ch] text-lg">
              Your Vedic birth chart, where every reading points to the placement behind it.
            </p>
            <div data-hero-line className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-3">
              <Link href="/onboarding" className="btn">
                Calculate my chart <Arrow />
              </Link>
              <span className="pen text-lg">free</span>
            </div>
          </div>

          <figure className="w-full max-w-[28rem] lg:justify-self-end" aria-label="A sample chart, with Venus exalted in the 1st house circled">
            <div inert>
              <SouthIndianChart kundli={SAMPLE} selection={{ kind: "planet", name: "Venus" }} onSelect={noop} />
            </div>
            <figcaption className="mt-5" style={{ lineHeight: "var(--line)" }}>
              <span data-write className="block font-medium text-ink">
                Often an easy warmth with people. <Tick data-hero-tick="" className="ml-1" />
              </span>
              <span data-hero-note className="pen block text-lg">
                because Venus is exalted in your 1st house
              </span>
            </figcaption>
          </figure>
        </section>

        <Question n="Q2." title="Don't know your birth time?" prose="That's fine. We say what can't be known, and read from your Moon sign.">
          <div data-answer style={{ lineHeight: "var(--line)" }}>
            <AnswerRow label="Exact time">
              <Term en="Lagna" deva="लग्न" />
              <Tick data-scroll-tick="" className="ml-2" />
            </AnswerRow>
            <AnswerRow label="Roughly, or not at all">
              <Struck>Lagna</Struck> Moon sign
              <Tick data-scroll-tick="" className="ml-2" />
            </AnswerRow>
          </div>
        </Question>

        <Question n="Q3." title="Is the maths right?">
          <ul data-answer style={{ lineHeight: "var(--line)" }}>
            {["The astronomy serious Jyotish software uses", "Checked against reference charts", "Open source, so anyone can check"].map((line) => (
              <li key={line} className="flex items-start gap-2">
                <Tick data-scroll-tick="" className="mt-1.5" />
                <span data-scroll-write className="text-ink">
                  {line}
                </span>
              </li>
            ))}
          </ul>
        </Question>

        <Question n="Q4." title="Who sees my details?" prose="It's free. These never reach the AI that words your readings.">
          <div data-answer style={{ lineHeight: "var(--line)" }}>
            {["Your name", "Your email", "Your birthplace"].map((fact) => (
              <p key={fact}>
                <Struck>{fact}</Struck>
              </p>
            ))}
          </div>
        </Question>

        <section className="border-t border-rule-strong/70 py-20 lg:py-24">
          <h2 data-reveal className="serif max-w-[15ch] text-[clamp(2.6rem,5.5vw,4.6rem)]">
            Your turn.
          </h2>
          <div data-reveal className="mt-8">
            <Link href="/onboarding" className="btn">
              Calculate my chart <Arrow />
            </Link>
          </div>
        </section>
      </main>
    </Sheet>
  );
}

/** Later questions keep Q1's split: the question left, the short answer right. */
function Question({ n, title, prose, children }: { n: string; title: string; prose?: string; children: React.ReactNode }) {
  return (
    <section className={`relative ${SPLIT} border-t border-rule-strong/70 py-16 lg:py-20`}>
      <div className="relative">
        <MarginLabel className="top-2 lg:top-3">{n}</MarginLabel>
        <h2 data-reveal className="serif max-w-[18ch] text-[clamp(2.1rem,3.6vw,3rem)]">
          {title}
        </h2>
        {prose && (
          <p data-reveal className="mt-5 max-w-[40ch]">
            {prose}
          </p>
        )}
      </div>
      <div className="lg:pt-3">{children}</div>
    </section>
  );
}

function AnswerRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-x-4 sm:grid-cols-[11rem_1fr]">
      <span className="text-sm leading-[var(--line)] text-muted">{label}</span>
      <span data-scroll-write className="text-ink">
        {children}
      </span>
    </div>
  );
}

/** Crossed out in red pen; the line is drawn across exactly the struck words. */
function Struck({ children }: { children: React.ReactNode }) {
  return (
    <span className="relative inline-block">
      <span className="text-muted">{children}</span>
      <span aria-hidden data-strike className="absolute top-1/2 left-[-2px] h-[2px] w-[calc(100%+4px)] origin-left -rotate-2 bg-pen/80" />
      <span className="sr-only"> (not included)</span>
    </span>
  );
}
