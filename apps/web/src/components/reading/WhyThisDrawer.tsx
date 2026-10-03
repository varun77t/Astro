import type { Statement } from "@/lib/types";

/** "The Sun is…" reads as "because the Sun is…"; planet names keep their capital. */
const midSentence = (text: string) => (/^(The|Your|No) /.test(text) ? text.charAt(0).toLowerCase() + text.slice(1) : text);

/** The working behind one line of a reading: the placements in red pen, then the rules they come from. */
export function WhyThisDrawer({ id, statements, open }: { id: string; statements: Statement[]; open: boolean }) {
  const reasons = [...new Set(statements.flatMap((s) => s.because.map((b) => b.text)))];
  return (
    <div id={id} hidden={!open} className="pt-1 pb-4 motion-safe:animate-[why-open_260ms_ease-out]">
      <div className="border-l-2 border-pen/30 pl-4">
        <ul className="pen text-lg leading-7">
          {reasons.map((text, i) => (
            <li key={text}>
              {i === 0 ? "because " : "and "}
              {midSentence(text)}
            </li>
          ))}
        </ul>
        {statements.some((s) => s.certainty === "possible") && (
          <p className="mt-1 text-sm text-ink-2">A slightly different birth time would change this, so treat it as possible.</p>
        )}
        <ul className="mt-1 text-xs text-muted">
          {statements.map((s) => (
            <li key={s.rule_id}>
              {s.title} · {s.source}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
