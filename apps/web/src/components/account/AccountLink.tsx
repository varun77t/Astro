"use client";

import Link from "next/link";
import { useSession } from "@/lib/session";

/** Header link: "Sign in" for visitors, "Your charts" once signed in. Empty while loading, so it never flickers. */
export function AccountLink() {
  const session = useSession();
  if (session.status === "loading") return <span className="w-20" aria-hidden />;
  return session.status === "signed-in" ? (
    <Link href="/charts" className="link text-sm">
      Your charts
    </Link>
  ) : (
    <Link href="/login" className="link text-sm">
      Sign in
    </Link>
  );
}
