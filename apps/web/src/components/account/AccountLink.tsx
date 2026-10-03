"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { useSession } from "@/lib/session";
import { supabase } from "@/lib/supabase";

/** Header: "Sign in" for visitors; a profile menu once signed in. Empty while loading, so it never flickers. */
export function AccountLink() {
  const session = useSession();
  if (session.status === "loading") return <span className="size-9" aria-hidden />;
  if (session.status === "signed-out") {
    return (
      <Link href="/login" className="link text-sm">
        Sign in
      </Link>
    );
  }
  return <ProfileMenu email={session.user.email ?? ""} />;
}

/** The initial in a ring opens a small menu: who's signed in, their charts, the account page, sign out. */
function ProfileMenu({ email }: { email: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  // Close on a click elsewhere or Escape (returning focus to the button).
  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        button.current?.focus();
      }
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function signOut() {
    setOpen(false);
    await supabase().auth.signOut();
    router.replace("/");
  }

  const item = "block w-full px-4 py-2 text-left text-sm text-ink-2 transition-colors hover:bg-bone hover:text-ink";

  return (
    <div ref={root} className="relative">
      <button
        ref={button}
        type="button"
        aria-haspopup="true"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={`Account menu for ${email}`}
        onClick={() => setOpen((o) => !o)}
        className={`flex size-9 items-center justify-center rounded-full border text-sm font-medium uppercase transition-colors ${
          open ? "border-ink bg-ink text-paper" : "border-rule-strong bg-paper text-ink hover:border-ink"
        }`}
      >
        {email.charAt(0) || "?"}
      </button>

      {open && (
        <div
          id={menuId}
          className="absolute top-full right-0 z-40 mt-2 w-60 overflow-hidden rounded-lg border border-rule bg-paper py-1 shadow-[0_8px_24px_rgba(0,0,0,0.06)] motion-safe:animate-[why-open_180ms_ease-out]"
        >
          <p className="border-b border-rule px-4 pt-2 pb-3">
            <span className="block text-xs text-muted">Signed in as</span>
            <span className="block truncate text-sm text-ink" title={email}>
              {email}
            </span>
          </p>
          <ul className="py-1">
            <li>
              <Link href="/charts" className={item} onClick={() => setOpen(false)}>
                Your charts
              </Link>
            </li>
            <li>
              <Link href="/account" className={item} onClick={() => setOpen(false)}>
                Account
              </Link>
            </li>
          </ul>
          <div className="border-t border-rule py-1">
            <button type="button" className={item} onClick={signOut}>
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
