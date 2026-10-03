"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FieldError } from "@/components/forms/Question";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { deleteAccount } from "@/lib/profiles";
import { useSession } from "@/lib/session";
import { supabase } from "@/lib/supabase";

export default function AccountPage() {
  const router = useRouter();
  const session = useSession();

  useEffect(() => {
    if (session.status === "signed-out") router.replace("/login?next=/account");
  }, [session.status, router]);

  return (
    <Sheet>
      <main className={`${SHEET_X} pt-10 pb-24`}>
        <div className="max-w-3xl">
          <h1 className="serif mt-7 text-[clamp(2.8rem,6vw,4.4rem)]">Your account.</h1>
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
    <section className="mt-10" aria-label="Account">
      <p className="text-sm text-muted">Signed in as</p>
      <p className="text-lg text-ink">{email}</p>
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
