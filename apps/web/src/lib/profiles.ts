"use client";

import { supabase } from "./supabase";
import type { BirthInput, Chart } from "./types";

/** Bump when the consent wording in SaveChart changes; each profile records which it agreed to. */
export const CONSENT_VERSION = "2026-10-03";

/** A saved person: what was asked at onboarding, plus a label and the consent to store it. */
export type SavedProfile = {
  id: string;
  label: string;
  birth_date: string;
  birth_time: string | null;
  time_accuracy: BirthInput["time_accuracy"];
  time_window_minutes: number | null;
  place_name: string;
  lat: number;
  lon: number;
  tz_name: string;
  fold: 0 | 1 | null;
  utc_offset_minutes: number | null;
  created_at: string;
};

/** The few chart facts the list shows, read from the stored chart. */
export type ProfileSummary = SavedProfile & { lagna: string | null; moonSign: string | null };

const COLUMNS =
  "id,label,birth_date,birth_time,time_accuracy,time_window_minutes,place_name,lat,lon,tz_name,fold,utc_offset_minutes,created_at";

/** Back to the API's input. Postgres returns times as HH:MM:SS; the API takes HH:MM. */
export function toBirthInput(p: SavedProfile): BirthInput {
  return {
    date: p.birth_date,
    time: p.birth_time ? p.birth_time.slice(0, 5) : null,
    time_accuracy: p.time_accuracy,
    time_window_minutes: p.time_window_minutes,
    tz_name: p.tz_name,
    lat: p.lat,
    lon: p.lon,
    fold: p.fold,
    utc_offset_minutes: p.utc_offset_minutes,
  };
}

function fail(error: { message: string } | null): void {
  if (error) throw new Error(error.message);
}

/** Store a person and their chart. Needs a signed-in user and their consent. */
export async function saveProfile(birth: BirthInput, placeName: string, label: string, chart: Chart): Promise<string> {
  const db = supabase();
  const { data, error } = await db
    .from("profiles")
    .insert({
      label: label.trim(),
      birth_date: birth.date,
      birth_time: birth.time,
      time_accuracy: birth.time_accuracy,
      time_window_minutes: birth.time_window_minutes,
      place_name: placeName,
      lat: birth.lat,
      lon: birth.lon,
      tz_name: birth.tz_name,
      fold: birth.fold,
      utc_offset_minutes: birth.utc_offset_minutes,
      consented_at: new Date().toISOString(),
      consent_version: CONSENT_VERSION,
    })
    .select("id")
    .single();
  fail(error);
  const id = (data as { id: string }).id;
  const res = await db.from("charts").insert({ profile_id: id, chart_json: chart, engine_version: chart.meta.engine_version });
  if (res.error) {
    await db.from("profiles").delete().eq("id", id); // don't leave a profile without its chart
    fail(res.error);
  }
  return id;
}

export async function listProfiles(): Promise<ProfileSummary[]> {
  const { data, error } = await supabase()
    .from("profiles")
    .select(`${COLUMNS},charts(sign:chart_json->ascendant->>sign,reliability:chart_json->reliability)`)
    .order("created_at", { ascending: true });
  fail(error);
  type Facts = { sign: string | null; reliability: Chart["reliability"] | null };
  type Row = SavedProfile & { charts: Facts | Facts[] | null };
  return ((data ?? []) as unknown as Row[]).map(({ charts: raw, ...p }) => {
    // One chart per profile; PostgREST may still hand it back as a one-item list.
    const charts = Array.isArray(raw) ? raw[0] : raw;
    const r = charts?.reliability;
    const lagnaKnown = r && r.time_accuracy !== "unknown" && r.basis === "ascendant";
    return {
      ...p,
      lagna: lagnaKnown ? (charts?.sign ?? null) : null,
      moonSign: r?.moon_sign_reliable ? r.moon_signs[0] : null,
    };
  });
}

export async function getProfile(id: string): Promise<SavedProfile | null> {
  const { data, error } = await supabase().from("profiles").select(COLUMNS).eq("id", id).maybeSingle();
  fail(error);
  return data as SavedProfile | null;
}

/** Permanently removes one person and their chart. */
export async function deleteProfile(id: string): Promise<void> {
  const { error } = await supabase().from("profiles").delete().eq("id", id);
  fail(error);
}

/** Permanently removes the account and everything in it, then signs out. */
export async function deleteAccount(): Promise<void> {
  const db = supabase();
  const { error } = await db.rpc("delete_my_account");
  fail(error);
  await db.auth.signOut({ scope: "local" });
}
