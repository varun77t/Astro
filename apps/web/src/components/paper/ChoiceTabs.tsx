/** Pick one of a few views, marked like the current step: ink with a red-pen underline. A radio group underneath. */
export function ChoiceTabs<T extends string>({
  legend,
  name,
  value,
  options,
  onChange,
  vertical = false,
}: {
  legend: string;
  name: string;
  value: T;
  options: { value: T; label: React.ReactNode }[];
  onChange: (value: T) => void;
  /** A stacked list, e.g. in a side column, instead of a row. */
  vertical?: boolean;
}) {
  return (
    <fieldset className={vertical ? "flex flex-col items-start" : "flex flex-wrap items-baseline gap-x-5 gap-y-1"}>
      <legend className={vertical ? "mb-1 text-sm text-muted" : "float-left mr-1 text-sm text-muted"}>{legend}</legend>
      {options.map((o) => (
        <label key={o.value} className="relative cursor-pointer leading-[var(--line)]">
          <input
            type="radio"
            name={name}
            value={o.value}
            checked={value === o.value}
            onChange={() => onChange(o.value)}
            className="peer sr-only"
          />
          <span className="rounded-sm text-muted underline-offset-[6px] transition-colors duration-200 peer-checked:text-ink peer-checked:underline peer-checked:decoration-pen peer-checked:decoration-2 peer-focus-visible:outline-2 peer-focus-visible:outline-offset-3 peer-focus-visible:outline-ink hover:text-ink">
            {o.label}
          </span>
        </label>
      ))}
    </fieldset>
  );
}
