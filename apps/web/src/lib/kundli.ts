// The chart as the drawings see it: which planets sit in which sign, what counts as the
// 1st house, and how sure each mark is. South and North Indian charts both render this.
import type { Chart, Dignity } from "./types";

export const SIGNS = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
] as const;

export const SIGN_ABBR: Record<string, string> = {
  Aries: "Ari",
  Taurus: "Tau",
  Gemini: "Gem",
  Cancer: "Can",
  Leo: "Leo",
  Virgo: "Vir",
  Libra: "Lib",
  Scorpio: "Sco",
  Sagittarius: "Sag",
  Capricorn: "Cap",
  Aquarius: "Aqu",
  Pisces: "Pis",
};

export const SIGN_LORD: Record<string, string> = {
  Aries: "Mars",
  Taurus: "Venus",
  Gemini: "Mercury",
  Cancer: "Moon",
  Leo: "Sun",
  Virgo: "Mercury",
  Libra: "Venus",
  Scorpio: "Mars",
  Sagittarius: "Jupiter",
  Capricorn: "Saturn",
  Aquarius: "Saturn",
  Pisces: "Jupiter",
};

export const PLANET_ABBR: Record<string, string> = {
  Sun: "Su",
  Moon: "Mo",
  Mars: "Ma",
  Mercury: "Me",
  Jupiter: "Ju",
  Venus: "Ve",
  Saturn: "Sa",
  Rahu: "Ra",
  Ketu: "Ke",
};

export type Varga = "D1" | "D9";

/** Why a planet's sign might be wrong. */
export type Doubt = "window" | "boundary";

export type ChartMark = {
  name: string;
  abbr: string;
  /** Degrees into the sign; D1 only. */
  degree: number | null;
  retrograde: boolean;
  combust: boolean;
  /** Dignity by sign; D1 only. */
  dignity: Dignity | null;
  doubt: Doubt | null;
};

/** sure: the Lagna. likely: computed, but the time window reaches another sign. possible: one of those other signs. */
export type LagnaMark = "sure" | "likely" | "possible" | null;

export type ChartCell = {
  sign: string;
  signIndex: number;
  /** House number counted from the chart's 1st house. */
  house: number;
  lagna: LagnaMark;
  planets: ChartMark[];
};

export type Kundli = {
  varga: Varga;
  /** What the 1st house is: the Lagna, or the Moon's sign when the Lagna isn't known. */
  basis: "lagna" | "moon";
  firstSign: string;
  lagnaDegree: number | null;
  /** Indexed by sign: 0 = Aries ... 11 = Pisces. */
  cells: ChartCell[];
};

/** One arcminute: closer than this to a sign edge, other software may disagree on the sign. */
const BOUNDARY = 1 / 60;
const NAVAMSA = 30 / 9;

const signIndex = (sign: string) => SIGNS.indexOf(sign as (typeof SIGNS)[number]);

export function houseOf(sign: string, firstSign: string): number {
  return ((signIndex(sign) - signIndex(firstSign) + 12) % 12) + 1;
}

function nearEdge(degree: number, span: number): boolean {
  const into = degree % span;
  return into < BOUNDARY || span - into < BOUNDARY;
}

export function buildKundli(chart: Chart, varga: Varga): Kundli {
  const r = chart.reliability;
  const d9 = varga === "D9";
  const lagnaComputed = r.time_accuracy !== "unknown" && r.basis === "ascendant";
  const lagnaSign = d9 ? chart.divisional.D9.ascendant_sign : chart.ascendant.sign;
  const lagnaReliable = d9 ? r.navamsa_ascendant_reliable : r.ascendant_reliable;
  const possible = d9 ? r.navamsa_ascendant_signs : r.ascendant_signs;
  const moonReliable = d9 ? r.navamsa_moon_reliable : r.moon_sign_reliable;

  const placed = chart.planets.map((p) => {
    const sign = d9 ? chart.divisional.D9.planets.find((q) => q.name === p.name)!.sign : p.sign;
    const doubt: Doubt | null =
      p.name === "Moon" && !moonReliable ? "window" : nearEdge(p.degree_in_sign, d9 ? NAVAMSA : 30) ? "boundary" : null;
    const mark: ChartMark = {
      name: p.name,
      abbr: PLANET_ABBR[p.name] ?? p.name.slice(0, 2),
      degree: d9 ? null : p.degree_in_sign,
      retrograde: p.retrograde,
      combust: p.combust,
      dignity: d9 ? null : p.dignity,
      doubt,
    };
    return { sign, mark };
  });

  const moonSign = placed.find((p) => p.mark.name === "Moon")!.sign;
  const firstSign = lagnaComputed ? lagnaSign : moonSign;
  // With no time at all every sign is possible, which says nothing; mark none.
  const markPossible = possible.length < 12;

  const cells: ChartCell[] = SIGNS.map((sign, i) => {
    let lagna: LagnaMark = null;
    if (lagnaComputed && sign === lagnaSign) lagna = lagnaReliable ? "sure" : "likely";
    else if (markPossible && possible.includes(sign) && (!lagnaComputed || !lagnaReliable)) lagna = "possible";
    return {
      sign,
      signIndex: i,
      house: houseOf(sign, firstSign),
      lagna,
      planets: placed.filter((p) => p.sign === sign).map((p) => p.mark),
    };
  });

  return {
    varga,
    basis: lagnaComputed ? "lagna" : "moon",
    firstSign,
    lagnaDegree: lagnaComputed && !d9 ? chart.ascendant.degree_in_sign : null,
    cells,
  };
}

/** The cell in house n (1-12). */
export function cellInHouse(k: Kundli, house: number): ChartCell {
  return k.cells.find((c) => c.house === house)!;
}

// South Indian: signs are fixed, clockwise from Pisces in the top-left corner.
export const SOUTH_GRID: Record<string, [row: number, col: number]> = {
  Pisces: [0, 0],
  Aries: [0, 1],
  Taurus: [0, 2],
  Gemini: [0, 3],
  Cancer: [1, 3],
  Leo: [2, 3],
  Virgo: [3, 3],
  Libra: [3, 2],
  Scorpio: [3, 1],
  Sagittarius: [3, 0],
  Capricorn: [2, 0],
  Aquarius: [1, 0],
};

type Point = [number, number];

// North Indian: houses are fixed, the 1st at the top, counted anticlockwise. Coordinates in a 100×100 square.
export const NORTH_HOUSES: Record<number, { shape: Point[]; planets: Point; sign: Point }> = {
  1: { shape: [[50, 0], [75, 25], [50, 50], [25, 25]], planets: [50, 22], sign: [50, 42] },
  2: { shape: [[0, 0], [50, 0], [25, 25]], planets: [25, 8], sign: [25, 18] },
  3: { shape: [[0, 0], [25, 25], [0, 50]], planets: [8, 25], sign: [18, 25] },
  4: { shape: [[0, 50], [25, 25], [50, 50], [25, 75]], planets: [22, 50], sign: [42, 50] },
  5: { shape: [[0, 50], [25, 75], [0, 100]], planets: [8, 75], sign: [18, 75] },
  6: { shape: [[0, 100], [25, 75], [50, 100]], planets: [25, 92], sign: [25, 82] },
  7: { shape: [[50, 50], [75, 75], [50, 100], [25, 75]], planets: [50, 78], sign: [50, 58] },
  8: { shape: [[50, 100], [75, 75], [100, 100]], planets: [75, 92], sign: [75, 82] },
  9: { shape: [[100, 100], [75, 75], [100, 50]], planets: [92, 75], sign: [82, 75] },
  10: { shape: [[100, 50], [75, 75], [50, 50], [75, 25]], planets: [78, 50], sign: [58, 50] },
  11: { shape: [[100, 50], [75, 25], [100, 0]], planets: [92, 25], sign: [82, 25] },
  12: { shape: [[100, 0], [75, 25], [50, 0]], planets: [75, 8], sign: [75, 18] },
};

export function ordinal(n: number): string {
  const s = n % 100 >= 11 && n % 100 <= 13 ? "th" : (["th", "st", "nd", "rd"][n % 10] ?? "th");
  return `${n}${s}`;
}
