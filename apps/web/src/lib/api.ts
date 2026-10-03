import { accessToken } from "./supabase";
import type { Area, BirthInput, BirthResolution, Chart, Dasha, GlossaryEntry, Narration, Place, Readings } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly optionsUtc: string[] = [],
  ) {
    super(message);
  }
}

type ValidationIssue = { loc?: (string | number)[]; msg?: string };

/** Turn a FastAPI error body into an ApiError. Handles our {code, message} details and
 * Pydantic's list of validation issues. */
export function toApiError(status: number, body: unknown): ApiError {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail) && "code" in detail) {
    const d = detail as { code: string; message?: string; options_utc?: string[] };
    return new ApiError(d.message ?? "Something went wrong.", status, d.code, d.options_utc);
  }
  if (Array.isArray(detail)) {
    const message = (detail as ValidationIssue[]).map((issue) => (issue.msg ?? "Invalid value").replace(/^Value error, /, "")).join(" ");
    return new ApiError(message, status, "validation_error");
  }
  return new ApiError("Something went wrong. Please try again.", status, "unknown");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Can't reach the server. Check your connection and try again.", 0, "network");
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw toApiError(res.status, body);
  return body as T;
}

const postJson = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export async function searchPlaces(query: string, signal?: AbortSignal): Promise<Place[]> {
  const params = new URLSearchParams({ q: query, limit: "6" });
  const data = await request<{ results: Place[] }>(`/api/v1/geocode?${params}`, { signal });
  return data.results;
}

export function resolveBirth(birth: BirthInput): Promise<BirthResolution> {
  return request("/api/v1/birth/resolve", postJson(birth));
}

export function createChart(birth: BirthInput): Promise<Chart> {
  return request("/api/v1/chart", postJson(birth));
}

export function createDasha(birth: BirthInput): Promise<Dasha> {
  return request("/api/v1/dasha", postJson(birth));
}

/** Rule-based readings for all five life areas in one request. */
export function createReadings(birth: BirthInput): Promise<Readings> {
  return request("/api/v1/readings", postJson(birth));
}

/** One area written as prose. Slow on a cache miss (a model writes it), so callers show a waiting state. */
export async function narrateReading(birth: BirthInput, area: Area, signal?: AbortSignal): Promise<Narration> {
  // Signed-in users get a bigger daily allowance of AI-written readings.
  const token = await accessToken().catch(() => null);
  const init = postJson(birth);
  if (token) init.headers = { ...init.headers, Authorization: `Bearer ${token}` };
  return request(`/api/v1/readings/${area}/narration`, { ...init, signal });
}

let glossaryRequest: Promise<Map<string, GlossaryEntry>> | null = null;

/** The plain-language glossary, fetched once and shared. A failed fetch can be retried. */
export function loadGlossary(): Promise<Map<string, GlossaryEntry>> {
  glossaryRequest ??= request<{ entries: GlossaryEntry[] }>("/api/v1/glossary")
    .then(({ entries }) => new Map(entries.map((e) => [e.id, e])))
    .catch((err) => {
      glossaryRequest = null;
      throw err;
    });
  return glossaryRequest;
}
