"use client";

import { useEffect } from "react";
import { useAuth } from "./AuthProvider";

/**
 * Silently records real time-on-site for signed-in users.
 *
 * Sends a heartbeat to the backend every ~30s while the tab is visible and the
 * user is authenticated, so the Progress page can show genuine "time on site"
 * instead of a hardcoded number. No data is sent for visitors who aren't logged
 * in, and nothing is counted while the tab is hidden (background/locked).
 */
const HEARTBEAT_SECONDS = 30;

export function ActivityTracker() {
  const { session } = useAuth();
  const token = session?.access_token;

  useEffect(() => {
    if (!token) return;

    const send = () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
      fetch("/api/progress/track", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          kind: "site",
          seconds: HEARTBEAT_SECONDS,
          path: typeof location !== "undefined" ? location.pathname : null,
        }),
      }).catch(() => {
        /* best effort; never crash the UI */
      });
    };

    // Send once shortly after load, then on an interval while the app is open.
    const first = setTimeout(send, 2000);
    const id = setInterval(send, HEARTBEAT_SECONDS * 1000);
    const onVisible = () => {
      if (document.visibilityState === "visible") send();
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      clearTimeout(first);
      clearInterval(id);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [token]);

  return null;
}
