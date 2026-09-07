"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthProvider";

/**
 * Live time-on-site timer.
 *
 * Shows a ticking clock of how long you've been on MEDFREE in this session, and
 * the real total time tracked on your account (from the backend heartbeats).
 * Only counts while you're signed in and the tab is visible, so it's genuine
 * presence, not a fake number.
 */
function fmt(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
}

export function TimeOnSiteTimer({ compact = false }: { compact?: boolean }) {
  const { session } = useAuth();
  const token = session?.access_token;
  const [sessionSeconds, setSessionSeconds] = useState(0);
  const [totalSeconds, setTotalSeconds] = useState(0);
  const [loaded, setLoaded] = useState(false);

  // Pull real total tracked time once, on auth.
  useEffect(() => {
    if (!token) {
      setTotalSeconds(0);
      setLoaded(false);
      return;
    }
    let alive = true;
    fetch("/api/progress/overview", {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!alive || !d) return;
        setTotalSeconds(Number(d.time_on_site_seconds) || 0);
        setLoaded(true);
      })
      .catch(() => {
        if (alive) setLoaded(true);
      });
    return () => {
      alive = false;
    };
  }, [token]);

  // Tick a live session timer while visible + signed in.
  useEffect(() => {
    if (!token) return;
    const first = setTimeout(() => setSessionSeconds((s) => s + 1), 1000);
    const id = setInterval(() => {
      if (document.visibilityState !== "visible") return;
      setSessionSeconds((s) => s + 1);
    }, 1000);
    return () => {
      clearTimeout(first);
      clearInterval(id);
    };
  }, [token]);

  // Refresh the total every 30s so it stays in sync with the backend heartbeats.
  useEffect(() => {
    if (!token) return;
    const id = setInterval(async () => {
      try {
        const r = await fetch("/api/progress/overview", {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        });
        if (!r.ok) return;
        const d = await r.json();
        setTotalSeconds(Number(d.time_on_site_seconds) || 0);
      } catch {
        /* best effort */
      }
    }, 30000);
    return () => clearInterval(id);
  }, [token]);

  if (!token) return null;

  const totalLive = totalSeconds + sessionSeconds;

  if (compact) {
    if (!loaded) return null;
    return (
      <span className="inline-flex items-center gap-1.5 rounded-lg bg-surface-2 px-2.5 py-1 text-xs text-ink-2" title="Time on MEDFREE">
        <span className="relative flex h-1.5 w-1.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-60" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
        </span>
        {fmt(totalLive)}
      </span>
    );
  }

  return (
    <div className="rounded-xl bg-surface-1 p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Time on site</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-ink-1">{fmt(totalLive)}</p>
      <p className="mt-1 text-xs text-ink-3">
        {sessionSeconds > 0 ? (
          <>This session: {fmt(sessionSeconds)}</>
        ) : (
          "Only counts while you're signed in and the tab is visible."
        )}
      </p>
    </div>
  );
}
