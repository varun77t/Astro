"use client";

import { useId, useState } from "react";
import { FieldError } from "@/components/forms/Question";
import { ChoiceTabs } from "@/components/paper/ChoiceTabs";
import { supabase } from "@/lib/supabase";

type Mode = "sign-in" | "sign-up";

const MIN_PASSWORD = 8;

/** Supabase's messages, said plainly. */
function explain(message: string): string {
  if (/invalid login credentials/i.test(message)) return "That email and password don't match.";
  if (/already registered|already exists/i.test(message)) return "There's already an account with that email. Sign in instead.";
  if (/email not confirmed/i.test(message)) return "Confirm your email first: open the link we sent you.";
  if (/rate limit|too many/i.test(message)) return "Too many attempts. Wait a minute and try again.";
  if (/network|fetch/i.test(message)) return "Can't reach the sign-in service. Check your connection.";
  return message;
}

/** Email and password, for signing in or creating an account. Calls `onDone` once signed in. */
export function AuthForm({ initialMode = "sign-in", onDone }: { initialMode?: Mode; onDone: () => void }) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const id = useId();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    if (mode === "sign-up" && password.length < MIN_PASSWORD) {
      setError(`Use at least ${MIN_PASSWORD} characters for the password.`);
      return;
    }
    setBusy(true);
    try {
      const auth = supabase().auth;
      const { data, error: err } =
        mode === "sign-in"
          ? await auth.signInWithPassword({ email: email.trim(), password })
          : await auth.signUp({ email: email.trim(), password });
      if (err) throw err;
      if (!data.session) {
        // Email confirmation is switched on for the project.
        setNotice("Check your email and open the link to confirm your account, then sign in here.");
        setMode("sign-in");
        return;
      }
      onDone();
    } catch (err) {
      setError(explain(err instanceof Error ? err.message : String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="max-w-sm space-y-6">
      <ChoiceTabs
        legend="Account"
        hideLegend
        name={`${id}-mode`}
        value={mode}
        onChange={(m) => {
          setMode(m);
          setError("");
        }}
        options={[
          { value: "sign-in", label: "Sign in" },
          { value: "sign-up", label: "Create account" },
        ]}
      />

      <div>
        <label htmlFor={`${id}-email`} className="text-sm text-muted">
          Email
        </label>
        <input
          id={`${id}-email`}
          type="email"
          autoComplete="email"
          required
          className="answer-line"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <div>
        <label htmlFor={`${id}-password`} className="text-sm text-muted">
          Password{mode === "sign-up" && <span className="text-muted"> (at least {MIN_PASSWORD} characters)</span>}
        </label>
        <input
          id={`${id}-password`}
          type="password"
          autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
          required
          minLength={mode === "sign-up" ? MIN_PASSWORD : undefined}
          className="answer-line"
          value={password}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : undefined}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <FieldError id={`${id}-error`}>{error}</FieldError>}
        {notice && (
          <p role="status" className="mt-2 text-sm text-ink-2">
            {notice}
          </p>
        )}
      </div>

      <button type="submit" className="btn" disabled={busy || !email || !password}>
        {busy ? "One moment…" : mode === "sign-in" ? "Sign in" : "Create account"}
      </button>
    </form>
  );
}
