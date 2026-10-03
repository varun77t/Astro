/** Red-pen marks. Drawn as SVG paths with pathLength=1 so motion can draw them in. */

type MarkProps = { className?: string; "data-mark"?: string };

export function Tick({ className = "", ...rest }: MarkProps) {
  return (
    <svg
      width="22"
      height="18"
      viewBox="0 0 22 18"
      aria-hidden
      fill="none"
      className={`inline-block shrink-0 align-[-0.2em] ${className}`}
      {...rest}
    >
      <path
        d="M2 10 L8 15 L20 3"
        stroke="var(--pen)"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={1}
        strokeDasharray={1}
      />
    </svg>
  );
}

export function Cross({ className = "" }: { className?: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden fill="none" className={`inline-block shrink-0 ${className}`}>
      <path d="M2.5 2.5 L11.5 11.5 M11.5 2.5 L2.5 11.5" stroke="var(--pen)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function Arrow() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden fill="none">
      <path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** The question number written in the margin. Sits to the left of its column. */
export function MarginLabel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      aria-hidden
      className={`pen absolute -left-11 w-7 text-base leading-none sm:-left-20 sm:w-16 sm:text-right sm:text-xl ${className}`}
    >
      {children}
    </span>
  );
}

/** A marker's note: a red-pen heading over printed text, so it stays readable. */
export function PenNote({ label = "Note", children }: { label?: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-x-3 sm:grid-cols-[4.5rem_1fr]">
      <p className="pen text-lg leading-7">{label}</p>
      <p className="text-ink-2">{children}</p>
    </div>
  );
}

/** A Jyotish term with its Devanagari gloss. */
export function Term({ en, deva }: { en: string; deva: string }) {
  return (
    <>
      {en}{" "}
      <span lang="sa" className="font-deva text-[0.9em] text-muted">
        {deva}
      </span>
    </>
  );
}
