"use client";

import { useEffect, useState } from "react";
import { Arrow, PenNote, Tick } from "@/components/paper/Marks";
import { ApiError, resolveBirth } from "@/lib/api";
import { type BirthFormState, describeWindow, formatWallClock, toBirthInput } from "@/lib/birth";
import type { BirthResolution } from "@/lib/types";
import { TickOption } from "./Question";

export type ConfirmedOptions = { fold: 0 | 1 | null; utcOffsetMinutes: number | null };

type Props = {
  form: BirthFormState;
  onBack: () => void;
  onConfirm: (options: ConfirmedOptions) => void;
  busy: boolean;
  error?: string;
};

type State =
  | { kind: "loading" }
  | { kind: "resolved"; resolution: BirthResolution }
  | { kind: "ambiguous"; message: string; optionsUtc: string[] }
  | { kind: "error"; message: string };

export function ConfirmBirth({ form, onBack, onConfirm, busy, error }: Props) {
  const [options, setOptions] = useState<ConfirmedOptions>({ fold: null, utcOffsetMinutes: null });
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    resolveBirth(toBirthInput(form, options))
      .then((resolution) => !cancelled && setState({ kind: "resolved", resolution }))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.code === "ambiguous_local_time")
          setState({ kind: "ambiguous", message: err.message, optionsUtc: err.optionsUtc });
        else setState({ kind: "error", message: err instanceof Error ? err.message : String(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [form, options]);

  const place = form.place!;

  return (
    <div className="space-y-10">
      <div style={{ lineHeight: "var(--line)" }}>
        {state.kind === "resolved" ? (
          <Summary r={state.resolution} place={place.display_name} />
        ) : (
          <>
            <p className="text-xl text-ink">{place.display_name}</p>
            {state.kind === "loading" && (
              <p aria-live="polite" className="text-muted">
                Reading the time zone…
              </p>
            )}
          </>
        )}
      </div>

      {state.kind === "error" && (
        <div role="alert">
          <PenNote label="Stop">{state.message}</PenNote>
        </div>
      )}

      {state.kind === "ambiguous" && (
        <fieldset>
          <legend className="serif text-[1.9rem]">This time happened twice.</legend>
          <p className="mt-1 mb-3 text-muted">Clocks went back that night. Which one was it?</p>
          {state.optionsUtc.map((utc, i) => (
            <TickOption
              key={utc}
              name="fold"
              value={String(i)}
              checked={false}
              onChange={() => {
                setState({ kind: "loading" });
                setOptions((o) => ({ ...o, fold: i as 0 | 1 }));
              }}
              label={i === 0 ? "The first time" : "The second time"}
              hint={i === 0 ? "Before clocks went back" : "After clocks went back"}
            />
          ))}
        </fieldset>
      )}

      {state.kind === "resolved" && state.resolution.notes.map((note) => <PenNote key={note}>{note}</PenNote>)}

      {error && (
        <p role="alert" className="text-pen">
          {error}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-rule-strong/70 pt-8">
        {state.kind === "resolved" && (
          <button type="button" disabled={busy} onClick={() => onConfirm(options)} className="btn">
            {busy ? "Calculating…" : "Looks right"}
            {!busy && <Arrow />}
          </button>
        )}
        <button type="button" onClick={onBack} className="link">
          Edit
        </button>
      </div>
    </div>
  );
}

/** The answer in plain words: when, where, which clock. */
function Summary({ r, place }: { r: BirthResolution; place: string }) {
  return (
    <>
      <p className="text-xl text-ink">
        {r.time_assumed ? <>{formatWallClock(r.local_time).split(",")[0]}, time unknown</> : formatWallClock(r.local_time)}
        {r.time_accuracy === "approximate" && <span className="ml-2 text-base text-muted">± {describeWindow(r.window_minutes)}</span>}
      </p>
      <p className="text-ink-2">{place}</p>
      <p className="text-muted">
        {r.tz_abbreviation ? `${r.tz_abbreviation}, ` : ""}UTC{r.utc_offset}
        <Tick data-mark="confirm" className="ml-2" />
      </p>
    </>
  );
}
