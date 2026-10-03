import { describe, expect, it } from "vitest";
import { describeUncertainty, lifeLine, monthYear } from "./dasha";
import type { Dasha } from "./types";

const md = (lord: string, start: string, end: string) => ({ lord, start, end, antardashas: [] });

const dasha: Dasha = {
  moon_nakshatra: "Dhanishta",
  first_lord: "Mars",
  balance_years: 5,
  as_of: "2026-10-03T00:00:00Z",
  mahadashas: [
    md("Mars", "1988-05-17T00:00:00Z", "1995-05-17T00:00:00Z"),
    md("Rahu", "1995-05-17T00:00:00Z", "2013-05-17T00:00:00Z"),
    md("Jupiter", "2013-05-17T00:00:00Z", "2029-05-17T00:00:00Z"),
  ],
  current: {
    mahadasha: { lord: "Jupiter", start: "2013-05-17T00:00:00Z", end: "2029-05-17T00:00:00Z" },
    antardasha: { lord: "Saturn", start: "2025-01-01T00:00:00Z", end: "2027-01-01T00:00:00Z" },
    pratyantardasha: { lord: "Moon", start: "2026-09-01T00:00:00Z", end: "2026-12-01T00:00:00Z" },
  },
  pratyantardashas: [],
  timing_reliable: true,
  uncertainty_days: 8,
};

describe("lifeLine", () => {
  const { segments, now } = lifeLine(dasha, "1990-05-17T00:00:00Z");

  it("starts the line at birth, clipping the first period", () => {
    expect(segments[0].left).toBe(0);
    expect(segments[0].width).toBeCloseTo((5 / 39) * 100, 0);
  });

  it("fills the line exactly", () => {
    const last = segments[segments.length - 1];
    expect(last.left + last.width).toBeCloseTo(100, 6);
  });

  it("marks the current period and where now falls", () => {
    expect(segments.find((s) => s.isCurrent)?.lord).toBe("Jupiter");
    expect(now).toBeGreaterThan(segments[2].left);
    expect(now).toBeLessThan(100);
  });
});

describe("helpers", () => {
  it("formats months in UTC", () => {
    expect(monthYear("2029-05-31T23:30:00Z")).toBe("May 2029");
  });

  it("says nothing about small uncertainty and words the rest", () => {
    expect(describeUncertainty(8)).toBeNull();
    expect(describeUncertainty(null)).toBeNull();
    expect(describeUncertainty(45)).toBe("about 6 weeks");
    expect(describeUncertainty(200)).toBe("about 7 months");
    expect(describeUncertainty(900)).toBe("about 2 years");
  });
});
