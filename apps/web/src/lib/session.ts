"use client";

import type { User } from "@supabase/supabase-js";
import { useEffect, useState } from "react";
import { supabase } from "./supabase";

export type SessionState = { status: "loading" } | { status: "signed-out" } | { status: "signed-in"; user: User };

/** The current sign-in state, kept up to date as the user signs in or out (in any tab). */
export function useSession(): SessionState {
  const [state, setState] = useState<SessionState>({ status: "loading" });
  useEffect(() => {
    const auth = supabase().auth;
    auth
      .getSession()
      .then(({ data }) => setState(data.session ? { status: "signed-in", user: data.session.user } : { status: "signed-out" }));
    const { data } = auth.onAuthStateChange((_event, session) =>
      setState(session ? { status: "signed-in", user: session.user } : { status: "signed-out" }),
    );
    return () => data.subscription.unsubscribe();
  }, []);
  return state;
}
