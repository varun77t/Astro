"use client";

import { useEffect, useRef, useState } from "react";
import { ChoiceTabs } from "@/components/paper/ChoiceTabs";
import { narrateReading } from "@/lib/api";
import { narrationView, rulesView } from "@/lib/reading";
import type { Area, BirthInput, Narration, Readings as ReadingsData } from "@/lib/types";
import { ReadingCard, ReadingPending } from "./ReadingCard";

/** Longer than the server's own budget, so the server's rule-only answer normally arrives first. */
const NARRATION_TIMEOUT_MS = 40_000;

type Written = { narration: Narration } | { failed: true };

/** The five life areas: pick one in the margin, read it on the right. Each is written on first view. */
export function Readings({ data, birth }: { data: ReadingsData; birth: BirthInput }) {
  const [area, setArea] = useState<Area>(data.readings[0].area);
  const [written, setWritten] = useState<Partial<Record<Area, Written>>>({});
  const requested = useRef(new Set<Area>());
  const reading = data.readings.find((r) => r.area === area)!;

  // Ask for the area's written reading once; later visits reuse it.
  useEffect(() => {
    if (requested.current.has(area)) return;
    requested.current.add(area);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), NARRATION_TIMEOUT_MS);
    narrateReading(birth, area, ctrl.signal)
      .then(
        (narration) => setWritten((w) => ({ ...w, [area]: { narration } })),
        () => setWritten((w) => ({ ...w, [area]: { failed: true } })),
      )
      .finally(() => clearTimeout(timer));
  }, [area, birth]);

  const result = written[area];
  return (
    <section className="mt-24 grid gap-x-12 gap-y-10 border-t border-rule-strong/70 pt-14 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <div className="space-y-8 lg:sticky lg:top-8 lg:self-start">
        <div className="space-y-4">
          <h2 className="serif text-[clamp(2.2rem,4vw,3rem)]">Your readings.</h2>
          <p className="max-w-[40ch] text-ink-2">{data.note}</p>
        </div>
        <ChoiceTabs
          vertical
          legend="Area"
          name="reading-area"
          value={area}
          onChange={setArea}
          options={data.readings.map((r) => ({ value: r.area, label: r.title }))}
        />
      </div>

      <div className="lg:pt-3" aria-live="polite">
        {result === undefined ? (
          <ReadingPending />
        ) : (
          <ReadingCard key={area} view={"narration" in result ? narrationView(result.narration) : rulesView(reading)} />
        )}
      </div>
    </section>
  );
}
