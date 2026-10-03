import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { buildKundli, cellInHouse, houseOf, ordinal, SIGNS, SOUTH_GRID } from "./kundli";
import type { Chart } from "./types";

const fixture = (name: string): Chart => JSON.parse(readFileSync(resolve(__dirname, "__fixtures__", `${name}.json`), "utf8"));

const golden = (name: string) =>
  JSON.parse(readFileSync(resolve(__dirname, "../../../../data/golden_charts", `${name}.json`), "utf8")) as {
    expected: { ascendant: string; planets: Record<string, string> };
  };

const exact = fixture("bengaluru-1990-exact");
const placementOf = (k: ReturnType<typeof buildKundli>, planet: string) => k.cells.find((c) => c.planets.some((p) => p.name === planet))!;

describe("D1 against the reference software (bengaluru-1990)", () => {
  const k = buildKundli(exact, "D1");

  it("puts every planet in the reference sign", () => {
    for (const [planet, value] of Object.entries(golden("bengaluru-1990").expected.planets)) {
      expect(placementOf(k, planet).sign, planet).toBe(value.split(" ")[0]);
    }
  });

  it("matches AstroSage's houses from a Virgo Lagna", () => {
    const astroSage = { Sun: 9, Moon: 5, Mars: 6, Mercury: 8, Jupiter: 10, Venus: 7, Saturn: 5, Rahu: 5, Ketu: 11 };
    for (const [planet, house] of Object.entries(astroSage)) expect(placementOf(k, planet).house, planet).toBe(house);
    expect(k.basis).toBe("lagna");
    expect(k.firstSign).toBe("Virgo");
    expect(cellInHouse(k, 1).lagna).toBe("sure");
  });

  it("keeps 1-12 houses with one cell each", () => {
    expect(k.cells.map((c) => c.house).sort((a, b) => a - b)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
  });
});

// The classical navamsa rule, written independently of the engine's continuous formula:
// movable signs count from themselves, fixed signs from the 9th, dual signs from the 5th.
function classicalNavamsa(text: string): string {
  const [sign, dms] = text.split(" ");
  const [d, m, s] = dms.split(":").map(Number);
  const i = SIGNS.indexOf(sign as (typeof SIGNS)[number]);
  const part = Math.floor((d + m / 60 + s / 3600) / (30 / 9));
  const start = [0, 8, 4][i % 3];
  return SIGNS[(i + start + part) % 12];
}

describe("D9 against the classical rule", () => {
  for (const name of ["bengaluru-1990-exact", "sydney-2000-exact"]) {
    it(`${name}: every planet's navamsa`, () => {
      const chart = fixture(name);
      const ref = golden(name.replace("-exact", "")).expected.planets;
      const k = buildKundli(chart, "D9");
      for (const [planet, value] of Object.entries(ref)) {
        // Sydney's Venus sits on a sign edge, so the references disagree on its navamsa as well.
        if (name.startsWith("sydney") && planet === "Venus") continue;
        expect(placementOf(k, planet).sign, planet).toBe(classicalNavamsa(value));
      }
    });
  }
});

describe("uncertainty", () => {
  it("approximate time with a loose window counts houses from the Moon and marks possible Lagnas", () => {
    const k = buildKundli(fixture("bengaluru-1990-approx"), "D1");
    expect(k.basis).toBe("moon");
    expect(k.firstSign).toBe("Capricorn");
    expect(k.lagnaDegree).toBeNull();
    expect(k.cells.filter((c) => c.lagna === "possible").map((c) => c.sign)).toEqual(["Leo", "Virgo", "Libra"]);
    expect(k.cells.some((c) => c.lagna === "sure" || c.lagna === "likely")).toBe(false);
  });

  it("unknown time marks no Lagna and doubts the Moon when it changed sign", () => {
    const k = buildKundli(fixture("bengaluru-1990-unknown"), "D1");
    expect(k.cells.some((c) => c.lagna)).toBe(false);
    expect(placementOf(k, "Moon").planets.find((p) => p.name === "Moon")!.doubt).toBe("window");
  });

  it("an exact time whose navamsa Lagna straddles two signs is only likely", () => {
    const k = buildKundli(fixture("sydney-2000-exact"), "D9");
    expect(k.basis).toBe("lagna");
    expect(k.cells.find((c) => c.sign === "Pisces")!.lagna).toBe("likely");
    expect(k.cells.find((c) => c.sign === "Aries")!.lagna).toBe("possible");
  });

  it("flags a planet within an arcminute of a sign edge", () => {
    const venus = placementOf(buildKundli(fixture("sydney-2000-exact"), "D1"), "Venus").planets.find((p) => p.name === "Venus")!;
    expect(venus.doubt).toBe("boundary");
  });
});

describe("helpers", () => {
  it("counts houses round the zodiac", () => {
    expect(houseOf("Virgo", "Virgo")).toBe(1);
    expect(houseOf("Leo", "Virgo")).toBe(12);
    expect(houseOf("Pisces", "Virgo")).toBe(7);
  });

  it("lays the South Indian grid clockwise round the edge", () => {
    expect(SOUTH_GRID.Pisces).toEqual([0, 0]);
    expect(SOUTH_GRID.Virgo).toEqual([3, 3]);
    expect(new Set(Object.values(SOUTH_GRID).map(String)).size).toBe(12);
  });

  it("writes ordinals", () => {
    expect([1, 2, 3, 4, 11, 12].map(ordinal)).toEqual(["1st", "2nd", "3rd", "4th", "11th", "12th"]);
  });
});
