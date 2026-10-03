"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FieldError } from "@/components/forms/Question";
import { Arrow } from "@/components/paper/Marks";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { deleteAccount, deleteProfile, listProfiles, type ProfileSummary } from "@/lib/profiles";
import { useSession } from "@/lib/session";
import { supabase } from "@/lib/supabase";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "1990-05-17" + "14:35:00" -> "17 May 1990, 14:35". The wall clock as entered, no timezone maths. */
function born(p: ProfileSummary): string {
  const [y, m, d] = p.birth_date.split("-").map(Number);
  const date = `${d} ${MONTHS[m - 1]} ${y}`;
  return p.birth_time ? `${date}, ${p.birth_time.slice(0, 5)}` : `${date}, time unknown`;
}

export default function ChartsPage() {
  const router = useRouter();
  const session = useSession();
  const [profiles, setProfiles] = useState<ProfileSummary[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (session.status === "signed-out") router.replace("/login?next=/charts");
    if (session.status !== "signed-in") return;
    listProfiles().then(setProfiles, (err: Error) => setError(err.message));
  }, [session.status, router]);

  async function remove(p: ProfileSummary) {
    if (!window.confirm(`Delete ${p.label}'s chart and birth details? This can't be undone.`)) return;
    try {
      await deleteProfile(p.id);
      setProfiles((list) => list?.filter((x) => x.id !== p.id) ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <Sheet>
      <main className={`${SHEET_X} pt-10 pb-24`}>
        <div className="max-w-3xl">
          <h1 className="serif mt-7 text-[clamp(2.8rem,6vw,4.4rem)]">Your charts.</h1>

          {error && <FieldError id="charts-error">{error}</FieldError>}

          {profiles === null && !error ? (
            <p className="mt-10 text-muted" role="status">
              Loading…
            </p>
          ) : (
            profiles && (
              <>
                {profiles.length === 0 ? (
                  <p className="mt-6 max-w-[46ch] text-lg">Nothing saved yet. Calculate a chart, then save it from the chart page.</p>
                ) : (
                  <ul className="mt-10 border-t border-rule-strong/70">
                    {profiles.map((p) => (
                      <li key={p.id} className="grid grid-cols-[1fr_auto] items-baseline gap-x-6 border-b border-rule py-4">
                        <Link href={`/chart/${p.id}`} className="group block">
                          <span className="text-lg text-ink underline-offset-[6px] group-hover:underline group-hover:decoration-pen group-hover:decoration-2">
                            {p.label}
                          </span>
                          <span className="mt-0.5 block text-sm text-muted">
                            {born(p)} · {p.place_name}
                          </span>
                          <span className="block text-sm text-ink-2">
                            {p.lagna ? `${p.lagna} Lagna` : "Lagna unknown"}
                            {p.moonSign && ` · Moon in ${p.moonSign}`}
                          </span>
                        </Link>
                        <button type="button" className="text-sm text-muted hover:text-pen" onClick={() => remove(p)}>
                          Delete
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                <Link href="/onboarding" className="btn mt-8">
                  New chart <Arrow />
                </Link>
              </>
            )
          )}

          {session.status === "signed-in" && <Account email={session.user.email ?? ""} />}
        </div>
      </main>
    </Sheet>
  );
}

/** Who's signed in, signing out, and deleting everything. */
function Account({ email }: { email: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function erase() {
    setBusy(true);
    setError("");
    try {
      await deleteAccount();
      router.replace("/?deleted=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  return (
    <section className="mt-24 border-t border-rule-strong/70 pt-10" aria-labelledby="account-heading">
      <h2 id="account-heading" className="text-sm text-muted">
        Account
      </h2>
      <p className="mt-2 text-ink">{email}</p>
      <button
        type="button"
        className="link mt-4 block"
        onClick={async () => {
          await supabase().auth.signOut();
          router.replace("/");
        }}
      >
        Sign out
      </button>

      <div className="mt-10 max-w-[52ch]">
        {!confirming ? (
          <button
            type="button"
            className="text-sm text-muted underline underline-offset-4 hover:text-pen"
            onClick={() => setConfirming(true)}
          >
            Delete my account and data
          </button>
        ) : (
          <div className="space-y-4 border-l-2 border-pen/40 pl-4">
            <p className="text-ink">
              This permanently deletes your account and every saved chart and birth detail in it. It can&rsquo;t be undone.
            </p>
            {error && <FieldError id="delete-error">{error}</FieldError>}
            <div className="flex flex-wrap items-center gap-6">
              <button type="button" className="btn !bg-pen" disabled={busy} onClick={erase}>
                {busy ? "Deleting…" : "Delete everything"}
              </button>
              <button type="button" className="link" onClick={() => setConfirming(false)}>
                Keep my account
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
