"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { AuthForm } from "@/components/account/AuthForm";
import { SHEET_X, Sheet } from "@/components/paper/Sheet";
import { useSession } from "@/lib/session";

/** Only same-site paths, so a crafted link can't send people elsewhere after signing in. */
function safeNext(value: string | null): string {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : "/charts";
}

function Login() {
  const router = useRouter();
  const params = useSearchParams();
  const next = safeNext(params.get("next"));
  const session = useSession();

  useEffect(() => {
    if (session.status === "signed-in") router.replace(next);
  }, [session.status, next, router]);

  return (
    <main className={`${SHEET_X} pt-10 pb-24`}>
      <div className="max-w-3xl">
        <h1 className="serif mt-7 text-[clamp(2.8rem,6vw,4.4rem)]">Your account.</h1>
        <p className="mt-4 max-w-[46ch] text-lg">Save charts for yourself and your family, and come back to them.</p>
        <div className="mt-10">
          <AuthForm initialMode={params.get("mode") === "sign-up" ? "sign-up" : "sign-in"} onDone={() => router.replace(next)} />
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Sheet>
      <Suspense>
        <Login />
      </Suspense>
    </Sheet>
  );
}
