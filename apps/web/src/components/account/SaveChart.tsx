"use client";

import Link from "next/link";
import { useId, useState } from "react";
import type { Answer } from "@/components/chart/ChartAnswer";
import { FieldError } from "@/components/forms/Question";
import { Tick } from "@/components/paper/Marks";
import { saveProfile } from "@/lib/profiles";
import { useSession } from "@/lib/session";
import { AuthForm } from "./AuthForm";

/** Save this chart to the account: sign in first if needed, name it, and agree to storing it. */
export function SaveChart({ answer, placeName }: { answer: Answer; placeName: string }) {
  const session = useSession();
  const [open, setOpen] = useState(false);
  const [label, setLabel] = useState("Me");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [savedId, setSavedId] = useState<string | null>(null);
  const id = useId();

  if (session.status === "loading") return null;

  if (savedId) {
    return (
      <p role="status" className="text-ink">
        Saved to your charts <Tick className="ml-1" />{" "}
        <Link href={`/chart/${savedId}`} className="link ml-2 text-sm">
          Open it
        </Link>
      </p>
    );
  }

  if (!open) {
    return (
      <button
        type="button"
        className="font-medium text-ink underline decoration-pen decoration-2 underline-offset-[6px]"
        onClick={() => setOpen(true)}
      >
        Save this chart
      </button>
    );
  }

  if (session.status === "signed-out") {
    // Once signed in, the session changes and the save form below takes over.
    return (
      <div className="basis-full space-y-3 border-t border-rule-strong/70 pt-5">
        <p className="text-sm text-muted">Sign in or create an account to save this chart.</p>
        <AuthForm onDone={() => {}} />
      </div>
    );
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!consent) {
      setError("Tick the box to agree to storing these details.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      setSavedId(await saveProfile(answer.birth, placeName, label, answer.chart));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} noValidate className="basis-full space-y-5 border-t border-rule-strong/70 pt-5 [&>*]:max-w-sm">
      <div>
        <label htmlFor={`${id}-label`} className="text-sm text-muted">
          Whose chart is this?
        </label>
        <input
          id={`${id}-label`}
          className="answer-line"
          maxLength={60}
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Me, Mum, Arjun…"
        />
      </div>
      <label className="flex cursor-pointer items-start gap-3 text-sm text-ink-2">
        <input
          type="checkbox"
          className="mt-1 size-4 shrink-0"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          aria-describedby={error ? `${id}-error` : undefined}
        />
        <span>
          Store this birth date, time and place in my account so I can come back to it. Only I can see it, and I can delete it any time.
        </span>
      </label>
      {error && <FieldError id={`${id}-error`}>{error}</FieldError>}
      <button type="submit" className="btn" disabled={busy || !label.trim()}>
        {busy ? "Saving…" : "Save to my charts"}
      </button>
    </form>
  );
}
