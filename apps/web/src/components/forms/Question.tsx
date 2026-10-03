import { Cross, MarginLabel } from "@/components/paper/Marks";

type Props = {
  n: string;
  title: string;
  /** Renders a fieldset/legend (for radio groups) instead of a labelled block. */
  group?: boolean;
  htmlFor?: string;
  children: React.ReactNode;
};

/** One question on the paper: number in the margin, the question in serif, the answer below. */
export function Question({ n, title, group = false, htmlFor, children }: Props) {
  const heading = "serif block text-[1.9rem] sm:text-[2.2rem]";
  if (group) {
    return (
      <fieldset className="relative">
        <legend className={`${heading} relative`}>
          <MarginLabel className="top-2.5">{n}</MarginLabel>
          {title}
        </legend>
        <div className="mt-4">{children}</div>
      </fieldset>
    );
  }
  return (
    <div className="relative">
      <MarginLabel className="top-2.5">{n}</MarginLabel>
      <label htmlFor={htmlFor} className={heading}>
        {title}
      </label>
      <div className="mt-3">{children}</div>
    </div>
  );
}

export function FieldError({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <p id={id} className="mt-2 flex items-center gap-2 text-sm text-pen">
      <Cross />
      {children}
    </p>
  );
}

type TickOptionProps = {
  name: string;
  value: string;
  checked: boolean;
  onChange: () => void;
  label: string;
  hint?: string;
};

/** A "tick one" row: a ruled square that gets a red-pen tick when chosen. */
export function TickOption({ name, value, checked, onChange, label, hint }: TickOptionProps) {
  return (
    <label className="group flex min-h-[calc(var(--line)*2)] cursor-pointer items-start gap-3 py-1">
      <input type="radio" name={name} value={value} checked={checked} onChange={onChange} className="peer sr-only" />
      <span className="relative mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-[3px] border border-ink-2 bg-paper transition-colors group-hover:border-ink peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-ink">
        <svg width="22" height="18" viewBox="0 0 22 18" aria-hidden fill="none" className="absolute -top-1 left-0.5">
          <path
            d="M2 10 L8 15 L20 3"
            stroke="var(--pen)"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            pathLength={1}
            strokeDasharray={1}
            strokeDashoffset={checked ? 0 : 1}
            className="transition-[stroke-dashoffset] duration-300 ease-out"
          />
        </svg>
      </span>
      <span>
        <span className="block font-medium text-ink">{label}</span>
        {hint && <span className="block text-sm text-muted">{hint}</span>}
      </span>
    </label>
  );
}
