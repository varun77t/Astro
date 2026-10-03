"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FieldError } from "@/components/forms/Question";
import { Arrow } from "@/components/paper/Marks";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { deleteProfile, listProfiles, type ProfileSummary } from "@/lib/profiles";
import { useSession } from "@/lib/session";

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
        </div>
      </main>
    </Sheet>
  );
}
