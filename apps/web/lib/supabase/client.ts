"use client";

import { createBrowserClient } from "@supabase/ssr";

/**
 * Browser Supabase client. The Backend verifies the resulting access token via
 * `SupabaseAuthProvider` (apps/api/app/core/auth.py).
 *
 * Populate NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.
 */
export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    // Graceful degrade for local/preview environments without credentials.
    return null;
  }
  return createBrowserClient(url, anonKey);
}
