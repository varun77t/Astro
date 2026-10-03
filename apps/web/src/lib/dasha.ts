import type { Dasha, DashaPeriod } from "./types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2029-05-19T21:46:00Z" -> "May 2029". Read in UTC so it can't drift with the viewer's zone. */
export function monthYear(iso: string): string {
  const d = new Date(iso);
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

export const yearOf = (iso: string) => new Date(iso).getUTCFullYear();

export type Segment = DashaPeriod & {
  /** Share of the line, 0-100, from birth to the end of the cycle. */
  left: number;
  width: number;
  isCurrent: boolean;
};

/** Mahadashas laid on a line that starts at birth: the first one is clipped to the part actually lived. */
export function lifeLine(dasha: Dasha, birthIso: string): { segments: Segment[]; now: number | null } {
  const from = Date.parse(birthIso);
  const to = Date.parse(dasha.mahadashas[dasha.mahadashas.length - 1].end);
  const at = (iso: string) => ((Math.max(Date.parse(iso), from) - from) / (to - from)) * 100;
  const current = dasha.current?.mahadasha.lord;
  const segments = dasha.mahadashas.map((m) => ({
    lord: m.lord,
    start: m.start,
    end: m.end,
    left: at(m.start),
    width: at(m.end) - at(m.start),
    isCurrent: m.lord === current,
  }));
  const nowMs = Date.parse(dasha.as_of);
  return { segments, now: nowMs >= from && nowMs <= to ? at(dasha.as_of) : null };
}

/** How far a loose birth time could move the dates, in words; null when it's too small to matter. */
export function describeUncertainty(days: number | null): string | null {
  if (days === null || days < 30) return null;
  if (days < 75) return `about ${Math.round(days / 7)} weeks`;
  if (days < 548) return `about ${Math.round(days / 30.4)} months`;
  const years = Math.round(days / 365.25);
  return `about ${years} year${years === 1 ? "" : "s"}`;
}
