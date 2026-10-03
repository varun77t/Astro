"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, searchPlaces } from "@/lib/api";
import type { Place } from "@/lib/types";
import { FieldError } from "./Question";

const MIN_QUERY_LENGTH = 3;
const DEBOUNCE_MS = 350;

type Props = {
  inputId: string;
  value: Place | null;
  onChange: (place: Place | null) => void;
  error?: string;
};

type Status = "idle" | "searching" | "done" | "error";

export function PlaceAutocomplete({ inputId, value, onChange, error }: Props) {
  const listId = `${inputId}-list`;
  const errorId = `${inputId}-error`;
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const q = query.trim();
    if (q.length < MIN_QUERY_LENGTH) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setStatus("searching");
      try {
        const places = await searchPlaces(q, controller.signal);
        setResults(places);
        setActive(places.length ? 0 : -1);
        setOpen(true);
        setStatus("done");
        setStatusMessage(places.length ? `${places.length} places found.` : "Not found. Try the nearest town; a few kilometres won't change your chart.");
      } catch (err) {
        if (controller.signal.aborted) return;
        setResults([]);
        setStatus("error");
        setStatusMessage(
          err instanceof ApiError && err.code === "geocoder_unavailable"
            ? "Place search isn't responding. Try again in a minute."
            : err instanceof Error
              ? err.message
              : "Search failed.",
        );
      }
    }, DEBOUNCE_MS);
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query]);

  function choose(place: Place) {
    onChange(place);
    setOpen(false);
    setQuery("");
    setResults([]);
    setStatus("idle");
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" && results.length) {
      e.preventDefault();
      setOpen(true);
      setActive((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp" && results.length) {
      e.preventDefault();
      setActive((i) => (i <= 0 ? results.length - 1 : i - 1));
    } else if (e.key === "Enter" && open && active >= 0) {
      e.preventDefault();
      choose(results[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  if (value) {
    return (
      <div className="flex items-end justify-between gap-4 border-b border-ink pb-2">
        <p id={inputId} tabIndex={-1} className="text-lg text-ink outline-none">
          {value.display_name}
        </p>
        <button
          type="button"
          className="link shrink-0 text-sm"
          onClick={() => {
            onChange(null);
            setTimeout(() => inputRef.current?.focus(), 0);
          }}
        >
          Change
        </button>
      </div>
    );
  }

  const showList = open && results.length > 0;
  return (
    <div className="relative">
      <input
        ref={inputRef}
        id={inputId}
        type="text"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={showList}
        aria-controls={listId}
        aria-activedescendant={showList && active >= 0 ? `${listId}-${active}` : undefined}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        autoComplete="off"
        placeholder="City, town or village"
        className="answer-line"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          if (e.target.value.trim().length < MIN_QUERY_LENGTH) {
            setResults([]);
            setOpen(false);
            setStatus("idle");
          }
        }}
        onKeyDown={onKeyDown}
        onFocus={() => results.length && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {showList && (
        <ul
          id={listId}
          role="listbox"
          aria-label="Matching places"
          className="absolute z-20 mt-1 max-h-80 w-full overflow-auto rounded-lg border border-rule bg-paper py-1 shadow-[0_18px_40px_-18px_rgba(17,17,17,0.18)]"
        >
          {results.map((place, i) => (
            <li
              key={`${place.display_name}-${place.lat}-${place.lon}`}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === active}
              aria-label={`${place.display_name}, time zone ${place.tz_name}`}
              className={`flex cursor-pointer items-baseline justify-between gap-4 px-3 py-2.5 ${i === active ? "bg-bone" : ""}`}
              onMouseDown={(e) => e.preventDefault()}
              onMouseEnter={() => setActive(i)}
              onClick={() => choose(place)}
            >
              <span className="text-ink">{place.display_name}</span>
              <span className="shrink-0 font-mono text-xs text-muted">{place.tz_name}</span>
            </li>
          ))}
        </ul>
      )}
      {error && <FieldError id={errorId}>{error}</FieldError>}
      <p role="status" aria-live="polite" className="mt-2 min-h-5 text-sm text-muted empty:mt-0 empty:min-h-0">
        {status === "searching" ? "Searching…" : status === "idle" ? "" : statusMessage}
      </p>
    </div>
  );
}

