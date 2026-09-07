"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Ad, Announcement } from "@/lib/studyApi";

/**
 * Displays the latest admin announcements plus any active, controlled
 * placement banner (an ad). Public endpoint returns only active, in-schedule
 * items — never draft/expired content and never non-admin-controlled ads.
 */
export function HomepageBanner() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [ad, setAd] = useState<Ad | null>(null);
  const [dismissed, setDismissed] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/announcements").then((r) => r.json()).then(setAnnouncements).catch(() => []);
    fetch("/api/ads?placement=homepage").then((r) => r.json()).then(setAd).catch(() => null);
  }, []);

  const visibleAnn = announcements.filter((a) => a.id !== Number(dismissed));

  if (!visibleAnn.length && !ad) return null;

  return (
    <div className="space-y-3">
      {visibleAnn.map((a) => (
        <div key={a.id}
          className="flex items-start justify-between gap-4 rounded-2xl border border-accent/30 bg-surface-1 px-4 py-3">
          <div>
            <p className="text-sm font-semibold text-accent">{a.title}</p>
            {a.body && <p className="mt-0.5 text-sm text-ink-2">{a.body}</p>}
            {a.link && (
              <Link href={a.link} className="mt-1 inline-block text-xs text-accent hover:underline">
                Learn more →
              </Link>
            )}
          </div>
          <button onClick={() => setDismissed(String(a.id))} aria-label="Dismiss"
            className="text-ink-3 hover:text-ink-1">✕</button>
        </div>
      ))}

      {ad && (
        <Link href={ad.target_url ?? "#"}
          className="block rounded-2xl border border-surface-2 bg-surface-2 px-4 py-3 transition hover:border-accent/40">
          <p className="text-sm font-semibold">{ad.title ?? "Featured"}</p>
          {ad.alt_text && <p className="text-xs text-ink-2">{ad.alt_text}</p>}
          <span className="mt-1 inline-block text-xs text-accent">Open →</span>
        </Link>
      )}
    </div>
  );
}
