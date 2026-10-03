"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { type Answer, ChartAnswer, loadAnswer } from "@/components/chart/ChartAnswer";
import { FieldError } from "@/components/forms/Question";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { getProfile, type SavedProfile, toBirthInput } from "@/lib/profiles";
import { useSession } from "@/lib/session";

/** A saved chart. The birth details come from the account; everything read from them is
 * calculated fresh, so it always reflects the current engine and today's running period. */
export default function SavedChartPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const session = useSession();
  const [profile, setProfile] = useState<SavedProfile | null>(null);
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (session.status === "signed-out") router.replace(`/login?next=/chart/${id}`);
    if (session.status !== "signed-in") return;
    let live = true;
    getProfile(id)
      .then(async (p) => {
        if (!p) throw new Error("This chart isn't in your account. It may have been deleted.");
        if (live) setProfile(p);
        const a = await loadAnswer(toBirthInput(p));
        if (live) setAnswer(a);
      })
      .catch((err: Error) => live && setError(err.message));
    return () => {
      live = false;
    };
  }, [id, session.status, router]);

  const header = (
    <>
      <Link href="/charts" className="link text-sm">
        Your charts
      </Link>
      <h1 className="serif mt-5 text-[clamp(2.2rem,4vw,3rem)]">{profile ? `${profile.label}.` : "Chart."}</h1>
      {profile && <p className="mt-2 text-sm text-muted">{profile.place_name}</p>}
    </>
  );

  return (
    <Sheet>
      <main className={`${SHEET_X} pt-8 pb-24 sm:pt-10`}>
        {answer ? (
          <ChartAnswer answer={answer} header={header} actions={null} />
        ) : (
          <div className="max-w-3xl">
            {header}
            {error ? (
              <div className="mt-8">
                <FieldError id="chart-error">{error}</FieldError>
              </div>
            ) : (
              <p className="pen mt-8 text-xl" role="status">
                Drawing your chart…
              </p>
            )}
          </div>
        )}
      </main>
    </Sheet>
  );
}
