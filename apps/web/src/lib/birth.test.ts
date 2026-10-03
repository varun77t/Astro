import { describe, expect, it } from "vitest";
import {
  type BirthFormState,
  emptyBirthForm,
  formatWallClock,
  toBirthInput,
  validateBirthForm,
} from "./birth";
import type { Place } from "./types";

const mysuru: Place = {
  name: "Mysuru",
  display_name: "Mysuru, Karnataka, India",
  lat: 12.3052,
  lon: 76.6554,
  country_code: "IN",
  tz_name: "Asia/Kolkata",
  source: "photon",
};
const filled: BirthFormState = { ...emptyBirthForm, date: "1990-05-17", time: "14:35", place: mysuru };
const TODAY = "2026-10-02";

describe("validateBirthForm", () => {
  it("accepts a complete form", () => {
    expect(validateBirthForm(filled, TODAY)).toEqual({});
  });

  it("requires date, time and place", () => {
    expect(Object.keys(validateBirthForm(emptyBirthForm, TODAY)).sort()).toEqual(["date", "place", "time"]);
  });

  it("does not require a time when it is unknown", () => {
    expect(validateBirthForm({ ...filled, time: "", timeAccuracy: "unknown" }, TODAY)).toEqual({});
  });

  it("rejects out-of-range and future dates", () => {
    expect(validateBirthForm({ ...filled, date: "1700-01-01" }, TODAY).date).toMatch(/1800/);
    expect(validateBirthForm({ ...filled, date: "2027-01-01" }, TODAY).date).toMatch(/future/);
  });
});

describe("toBirthInput", () => {
  it("maps an exact time", () => {
    expect(toBirthInput(filled)).toEqual({
      date: "1990-05-17",
      time: "14:35",
      time_accuracy: "exact",
      time_window_minutes: null,
      tz_name: "Asia/Kolkata",
      lat: 12.3052,
      lon: 76.6554,
      fold: null,
      utc_offset_minutes: null,
    });
  });

  it("sends the window only for approximate times", () => {
    const input = toBirthInput({ ...filled, timeAccuracy: "approximate", windowMinutes: 60 });
    expect(input.time_window_minutes).toBe(60);
  });

  it("drops the time when unknown and passes confirmation choices", () => {
    const input = toBirthInput({ ...filled, timeAccuracy: "unknown" }, { fold: 1, utcOffsetMinutes: 291 });
    expect(input.time).toBeNull();
    expect(input.fold).toBe(1);
    expect(input.utc_offset_minutes).toBe(291);
  });
});

describe("formatWallClock", () => {
  it("keeps the wall-clock time instead of converting to the viewer's zone", () => {
    expect(formatWallClock("1990-05-17T14:35:00+05:30")).toBe("17 May 1990, 14:35");
    expect(formatWallClock("1990-05-17T09:05:00Z")).toBe("17 May 1990, 09:05");
  });
});
