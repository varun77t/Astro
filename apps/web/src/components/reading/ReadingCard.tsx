"use client";

import { useId, useRef, useState } from "react";
import { EASE_OUT, gsap, MOTION_OK, useGSAP } from "@/lib/motion";
import { isPossible, type Point, type ReadingView } from "@/lib/reading";
import { WhyThisDrawer } from "./WhyThisDrawer";

/** One life area: the verdict, then what's for you, what's against you, and what the running period does. */
export function ReadingCard({ view }: { view: ReadingView }) {
  const [open, setOpen] = useState<string | null>(null);
  const root = useRef<HTMLDivElement>(null);
  const points = view.groups.flatMap((g) => g.points);

  useGSAP(
    () => {
      gsap.matchMedia().add(MOTION_OK, () => {
        gsap.from("[data-reading-in]", { autoAlpha: 0, x: -8, duration: 0.45, ease: EASE_OUT, stagger: 0.04 });
      });
    },
    { scope: root },
  );

  const toggle = (key: string) => setOpen((o) => (o === key ? null : key));

  return (
    <div ref={root} className="space-y-9">
      <p data-reading-in className="serif max-w-[34ch] text-[clamp(1.7rem,2.6vw,2.2rem)]">
        {view.summary}
      </p>

      {view.groups.map((g) =>
        g.points.length === 0 ? null : (
          <section key={g.label} aria-label={g.label}>
            <h3 data-reading-in className="mb-1 text-sm text-muted">
              {g.label}
            </h3>
            <ul className="border-t border-rule-strong/70">
              {g.points.map((p) => (
                <Line key={p.key} point={p} open={open === p.key} onToggle={() => toggle(p.key)} />
              ))}
            </ul>
          </section>
        ),
      )}

      {(points.some(isPossible) || view.disclaimer || view.quick) && (
        <div data-reading-in className="space-y-1 text-sm text-muted">
          {points.some(isPossible) && (
            <p>
              <span className="pen mr-1 text-lg leading-none">?</span> depends on your exact birth time.
            </p>
          )}
          {view.disclaimer && <p>{view.disclaimer}</p>}
          {view.quick && <p>Showing the quick version: each placement&rsquo;s reading as it stands.</p>}
        </div>
      )}
    </div>
  );
}

/** Ruled lines where the reading will be, while it's being written. */
export function ReadingPending() {
  return (
    <div className="space-y-9" aria-busy="true">
      <p className="pen text-xl" role="status">
        Writing your reading…
      </p>
      <div aria-hidden className="space-y-4">
        {[92, 78, 85, 60, 88].map((w, i) => (
          <span
            key={i}
            className="block h-3 rounded-full bg-rule-strong/60 motion-safe:animate-pulse"
            style={{ width: `${w}%`, animationDelay: `${i * 120}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

function Line({ point, open, onToggle }: { point: Point; open: boolean; onToggle: () => void }) {
  const drawer = useId();
  return (
    <li data-reading-in className="border-b border-rule">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={drawer}
        onClick={onToggle}
        className="group grid w-full grid-cols-[1fr_auto] items-baseline gap-x-6 py-3 text-left"
      >
        <span className="text-ink">
          {point.text}
          {isPossible(point) && (
            <>
              <span aria-hidden className="pen ml-2 text-lg leading-none">
                ?
              </span>
              <span className="sr-only"> (depends on your exact birth time)</span>
            </>
          )}
        </span>
        <span
          className={`text-sm whitespace-nowrap underline-offset-[5px] transition-colors duration-200 ${
            open ? "text-ink underline decoration-pen decoration-2" : "text-muted group-hover:text-ink"
          }`}
        >
          Why this?
        </span>
      </button>
      <WhyThisDrawer id={drawer} statements={point.statements} open={open} />
    </li>
  );
}
