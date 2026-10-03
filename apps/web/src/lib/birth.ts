import type { BirthInput, Place, TimeAccuracy } from "./types";

export type BirthFormState = {
  date: string;
  time: string;
  timeAccuracy: TimeAccuracy;
  windowMinutes: number;
  place: Place | null;
};

export type BirthFormErrors = Partial<Record<"date" | "time" | "place", string>>;

export const MIN_DATE = "1800-01-01";
export const MAX_DATE = "2100-12-31";
export const WINDOW_OPTIONS = [15, 30, 60, 120, 240];

export const emptyBirthForm: BirthFormState = {
  date: "",
  time: "",
  timeAccuracy: "exact",
  windowMinutes: 30,
  place: null,
};

export function validateBirthForm(form: BirthFormState, today: string): BirthFormErrors {
  const errors: BirthFormErrors = {};
  if (!form.date) errors.date = "Enter the date of birth.";
  else if (form.date < MIN_DATE || form.date > MAX_DATE) errors.date = "Birth year must be between 1800 and 2100.";
  else if (form.date > today) errors.date = "The date of birth can't be in the future.";

  if (form.timeAccuracy !== "unknown" && !form.time) errors.time = "Enter the time of birth, or choose “I don't know”.";

  if (!form.place) errors.place = "Choose the place of birth from the list.";
  return errors;
}

export function toBirthInput(form: BirthFormState, extras: { fold?: 0 | 1 | null; utcOffsetMinutes?: number | null } = {}): BirthInput {
  if (!form.place) throw new Error("place is required");
  return {
    date: form.date,
    time: form.timeAccuracy === "unknown" ? null : form.time,
    time_accuracy: form.timeAccuracy,
    time_window_minutes: form.timeAccuracy === "approximate" ? form.windowMinutes : null,
    tz_name: form.place.tz_name,
    lat: form.place.lat,
    lon: form.place.lon,
    fold: extras.fold ?? null,
    utc_offset_minutes: extras.utcOffsetMinutes ?? null,
  };
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Format the wall-clock part of an ISO string without converting it to the viewer's
 * timezone (a JS Date would silently shift it). "1990-05-17T14:35:00+05:30" ->
 * "17 May 1990, 14:35". */
export function formatWallClock(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso);
  if (!match) return iso;
  const [, y, mo, d, h, mi] = match;
  return `${Number(d)} ${MONTHS[Number(mo) - 1]} ${y}, ${h}:${mi}`;
}

export function describeWindow(minutes: number): string {
  if (minutes % 60 === 0) return `${minutes / 60} hour${minutes === 60 ? "" : "s"}`;
  return `${minutes} minutes`;
}

export function todayIso(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}
