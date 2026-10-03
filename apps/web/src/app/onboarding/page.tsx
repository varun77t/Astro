"use client";

import { useRef, useState } from "react";
import { SaveChart } from "@/components/account/SaveChart";
import { type Answer, ChartAnswer, loadAnswer } from "@/components/chart/ChartAnswer";
import { BirthForm } from "@/components/forms/BirthForm";
import { ConfirmBirth, type ConfirmedOptions } from "@/components/forms/ConfirmBirth";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { type BirthFormState, emptyBirthForm, toBirthInput } from "@/lib/birth";
import { EASE_OUT, gsap, MOTION_OK, useGSAP } from "@/lib/motion";

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
  const [answer, setAnswer] = useState<Answer | null>(null);
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
      setAnswer(await loadAnswer(toBirthInput(form, options)));
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
        {step === "chart" && answer ? (
          <ChartAnswer
            answer={answer}
            header={header}
            actions={
              // One row: the main action, then a quieter way out. An opened save form wraps to its own row.
              <div className="flex flex-wrap items-baseline gap-x-8 gap-y-5">
                <SaveChart answer={answer} placeName={form.place?.display_name ?? form.place?.name ?? ""} />
                <button
                  type="button"
                  className="text-sm text-muted underline decoration-rule-strong underline-offset-4 transition-colors hover:text-ink"
                  onClick={() => {
                    setAnswer(null);
                    setForm(emptyBirthForm);
                    go("form");
                  }}
                >
                  Start a new chart
                </button>
              </div>
            }
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
