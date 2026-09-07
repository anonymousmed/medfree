"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Session, SupabaseClient } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";

type AuthState = {
  session: Session | null;
  loading: boolean;
  supabase: SupabaseClient | null;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string) => Promise<{ error?: string; needsConfirm?: boolean }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error?: string }>;
};

const AuthContext = createContext<AuthState>({
  session: null,
  loading: true,
  supabase: null,
  signIn: async () => ({}),
  signUp: async () => ({}),
  signOut: async () => {},
  resetPassword: async () => ({}),
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [supabase, setSupabase] = useState<SupabaseClient | null | "unconfigured">(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const client = createClient();
    setSupabase(client ?? "unconfigured");
    if (!client) {
      setLoading(false);
      return;
    }
    client.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: sub } = client.auth.onAuthStateChange((_event, s) => {
      setSession(s);
      setLoading(false);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  const value: AuthState = {
    session,
    loading,
    supabase: supabase === "unconfigured" ? null : supabase,
    signIn: async (email, password) => {
      if (!supabase || supabase === "unconfigured") return { error: "Supabase not configured" };
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      return error ? { error: error.message } : {};
    },
    signUp: async (email, password) => {
      if (!supabase || supabase === "unconfigured") return { error: "Supabase not configured" };
      const { data, error } = await supabase.auth.signUp({ email, password });
      return error
        ? { error: error.message }
        : { needsConfirm: !data.session };
    },
    signOut: async () => {
      if (supabase && supabase !== "unconfigured") await supabase.auth.signOut();
    },
    resetPassword: async (email) => {
      if (!supabase || supabase === "unconfigured") return { error: "Supabase not configured" };
      const { error } = await supabase.auth.resetPasswordForEmail(email);
      return error ? { error: error.message } : {};
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
