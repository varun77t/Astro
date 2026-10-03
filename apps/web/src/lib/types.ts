// Mirrors the Pydantic schemas in apps/api/app/schemas.

export type TimeAccuracy = "exact" | "approximate" | "unknown";

export type Place = {
  name: string;
  display_name: string;
  lat: number;
  lon: number;
  country_code: string | null;
  tz_name: string;
  source: "photon" | "nominatim" | "manual";
};

export type BirthInput = {
  date: string; // YYYY-MM-DD
  time: string | null; // HH:MM
  time_accuracy: TimeAccuracy;
  time_window_minutes: number | null;
  tz_name: string;
  lat: number;
  lon: number;
  fold: 0 | 1 | null;
  utc_offset_minutes: number | null;
};

export type BirthResolution = {
  local_time: string; // ISO with offset, e.g. 1990-05-17T14:35:00+05:30
  utc: string; // ISO, e.g. 1990-05-17T09:05:00Z
  utc_offset: string;
  tz_name: string;
  tz_abbreviation: string | null;
  is_dst: boolean;
  offset_overridden: boolean;
  time_accuracy: TimeAccuracy;
  time_assumed: boolean;
  window_minutes: number;
  notes: string[];
};

export type ChartReliability = {
  time_accuracy: TimeAccuracy;
  window_minutes: number;
  ascendant_signs: string[];
  moon_signs: string[];
  moon_nakshatras: string[];
  ascendant_reliable: boolean;
  moon_sign_reliable: boolean;
  moon_nakshatra_reliable: boolean;
  navamsa_ascendant_signs: string[];
  navamsa_moon_signs: string[];
  navamsa_ascendant_reliable: boolean;
  navamsa_moon_reliable: boolean;
  basis: "ascendant" | "moon";
  warnings: string[];
};

export type Dignity = "exalted" | "debilitated" | "moolatrikona" | "own" | "friendly" | "neutral" | "enemy";

export type ChartPlanet = {
  name: string;
  sign: string;
  degree_in_sign: number;
  house: number;
  house_from_moon: number;
  nakshatra: string;
  pada: number;
  retrograde: boolean;
  combust: boolean;
  dignity: Dignity | null;
};

export type DivisionalChart = {
  ascendant_sign: string;
  planets: { name: string; sign: string; house: number }[];
};

// The parts the UI reads; the full JSON is also shown raw.
export type Chart = {
  meta: { utc: string; utc_offset: string; tz_name: string; engine_version: string; ayanamsa_value: number };
  reliability: ChartReliability;
  ascendant: { sign: string; degree_in_sign: number; nakshatra: string; pada: number };
  planets: ChartPlanet[];
  divisional: { D9: DivisionalChart };
};

export type GlossaryEntry = {
  id: string; // "planet.venus", "sign.pisces", "house.7", "dignity.exalted", "state.retrograde", "concept.lagna"
  kind: "planet" | "sign" | "house" | "dignity" | "state" | "concept";
  term: string;
  transliteration: string;
  sanskrit: string;
  short: string;
  body: string;
};

export type DashaPeriod = { lord: string; start: string; end: string };

export type Dasha = {
  moon_nakshatra: string;
  first_lord: string;
  balance_years: number;
  as_of: string;
  mahadashas: (DashaPeriod & { antardashas: DashaPeriod[] })[];
  current: { mahadasha: DashaPeriod; antardasha: DashaPeriod; pratyantardasha: DashaPeriod } | null;
  pratyantardashas: DashaPeriod[];
  timing_reliable: boolean;
  uncertainty_days: number | null;
};

export type Area = "education" | "career" | "money" | "health" | "relationships";

export type Because = { text: string; planets: string[]; houses: number[] };

export type Statement = {
  rule_id: string;
  title: string;
  text: string;
  tone: "supportive" | "cautionary" | "neutral";
  weight: number;
  /** "possible": holds at the given time, but another time inside the birth-time window would undo it. */
  certainty: "sure" | "possible";
  because: Because[];
  source: string;
};

export type Reading = {
  area: Area;
  title: string;
  basis: "ascendant" | "moon";
  summary: string;
  strengths: Statement[];
  watch_points: Statement[];
  current_period: Statement[];
  disclaimer: string | null;
  matched_rule_ids: string[];
};

export type Readings = { rules_version: string; as_of: string; note: string; readings: Reading[] };

export type NarratedPoint = { text: string; rule_ids: string[] };

/** A reading written as prose by a model ("llm"), or the rule texts as they are ("rules"). */
export type Narration = {
  area: Area;
  language: "en";
  mode: "llm" | "rules";
  provider: string | null;
  model: string | null;
  cached: boolean;
  summary: string;
  strengths: NarratedPoint[];
  watch_points: NarratedPoint[];
  current_period: NarratedPoint[];
  reading: Reading;
  rules_version: string;
};
