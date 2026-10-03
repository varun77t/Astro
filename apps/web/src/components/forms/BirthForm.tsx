"use client";

import { useState } from "react";
import { Arrow } from "@/components/paper/Marks";
import {
  type BirthFormErrors,
  type BirthFormState,
  describeWindow,
  MAX_DATE,
  MIN_DATE,
  todayIso,
  validateBirthForm,
  WINDOW_OPTIONS,
} from "@/lib/birth";
import type { TimeAccuracy } from "@/lib/types";
import { PlaceAutocomplete } from "./PlaceAutocomplete";
import { FieldError, Question, TickOption } from "./Question";

const ACCURACY_OPTIONS: { value: TimeAccuracy; label: string; hint: string }[] = [
  { value: "exact", label: "Exact", hint: "From a certificate" },
  { value: "approximate", label: "Roughly", hint: "Family memory, or rounded" },
  { value: "unknown", label: "I don't know", hint: "We'll use your Moon sign" },
];

type Props = {
  initial: BirthFormState;
  onSubmit: (form: BirthFormState) => void;
};

export function BirthForm({ initial, onSubmit }: Props) {
  const [form, setForm] = useState(initial);
  const [errors, setErrors] = useState<BirthFormErrors>({});
  const update = (patch: Partial<BirthFormState>) => {
    setForm((f) => ({ ...f, ...patch }));
    // An edited answer loses its old mark; a new one only appears on the next submit.
    setErrors((e) => {
      const next = { ...e };
      if ("date" in patch) delete next.date;
      if ("time" in patch || "timeAccuracy" in patch) delete next.time;
      if ("place" in patch) delete next.place;
      return next;
    });
  };

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const found = validateBirthForm(form, todayIso());
    setErrors(found);
    if (Object.keys(found).length === 0) onSubmit(form);
    else document.getElementById(found.date ? "birth-date" : found.time ? "birth-time" : "birth-place")?.focus();
  }

  return (
    <form noValidate onSubmit={submit} className="space-y-14">
      <Question n="Q1." title="When were you born?" htmlFor="birth-date">
        <input
          id="birth-date"
          type="date"
          min={MIN_DATE}
          max={MAX_DATE}
          className="answer-line max-w-xs"
          value={form.date}
          aria-invalid={Boolean(errors.date)}
          aria-describedby={errors.date ? "birth-date-error" : undefined}
          onChange={(e) => update({ date: e.target.value })}
        />
        {errors.date && <FieldError id="birth-date-error">{errors.date}</FieldError>}
      </Question>

      <Question n="Q2." title="How sure are you of the time?" group>
        <div>
          {ACCURACY_OPTIONS.map((opt) => (
            <TickOption
              key={opt.value}
              name="time-accuracy"
              value={opt.value}
              checked={form.timeAccuracy === opt.value}
              onChange={() => update({ timeAccuracy: opt.value })}
              label={opt.label}
              hint={opt.hint}
            />
          ))}
        </div>

        {form.timeAccuracy !== "unknown" ? (
          <div className="mt-7 grid gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="birth-time" className="block text-sm text-muted">
                Time of birth
              </label>
              <input
                id="birth-time"
                type="time"
                className="answer-line"
                value={form.time}
                aria-invalid={Boolean(errors.time)}
                aria-describedby={errors.time ? "birth-time-error" : undefined}
                onChange={(e) => update({ time: e.target.value })}
              />
              {errors.time && <FieldError id="birth-time-error">{errors.time}</FieldError>}
            </div>
            {form.timeAccuracy === "approximate" && (
              <div>
                <label htmlFor="time-window" className="block text-sm text-muted">
                  Accurate to within
                </label>
                <select
                  id="time-window"
                  className="answer-line"
                  value={form.windowMinutes}
                  onChange={(e) => update({ windowMinutes: Number(e.target.value) })}
                >
                  {WINDOW_OPTIONS.map((m) => (
                    <option key={m} value={m}>
                      ± {describeWindow(m)}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        ) : null}
      </Question>

      <Question n="Q3." title="Where were you born?" htmlFor="birth-place">
        <PlaceAutocomplete inputId="birth-place" value={form.place} error={errors.place} onChange={(place) => update({ place })} />
      </Question>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-rule-strong/70 pt-8">
        <button type="submit" className="btn">
          Continue <Arrow />
        </button>
      </div>
    </form>
  );
}
