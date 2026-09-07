"use client";

import { useState } from "react";
import { Button } from "@medfree/ui";

const CATEGORIES = [
  ["medical_error", "Medical error"],
  ["typo", "Typo"],
  ["broken_link", "Broken link"],
  ["incorrect_image", "Incorrect image"],
  ["copyright_issue", "Copyright/license issue"],
  ["outdated", "Outdated information"],
  ["inappropriate", "Inappropriate content"],
  ["technical", "Technical problem"],
];

/**
 * "Report an error" — surfaced on content pages (spec §36). Anonymous-friendly,
 * rate-limited, and queued for admin review.
 */
export function ReportError({
  target_type,
  target_slug,
  target_id,
}: {
  target_type: string;
  target_slug?: string;
  target_id?: number;
}) {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState("medical_error");
  const [detail, setDetail] = useState("");
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const res = await fetch("/api/resources/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_type, target_slug, target_id, category, detail: detail || undefined }),
      });
      if (!res.ok) throw new Error("Could not submit report");
      setDone(true);
    } catch (e: any) {
      setErr(e?.message ?? "Failed to submit.");
    }
  }

  if (done) {
    return (
      <button onClick={() => { setDone(false); setDetail(""); setOpen(false); }}
        className="text-sm text-accent underline-offset-2 hover:underline">
        Report an error ✓ (thanks!)
      </button>
    );
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)}
        className="text-sm text-ink-3 underline-offset-2 hover:text-ink-1 hover:underline">
        Report an error
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-xl border border-surface-2 bg-surface-1 p-4">
      <p className="text-sm font-semibold">Report an error</p>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map(([v, l]) => (
          <button type="button" key={v} onClick={() => setCategory(v)}
            className={`rounded-full px-3 py-1 text-xs ${category === v ? "bg-accent text-white" : "border border-surface-2 text-ink-2"}`}>
            {l}
          </button>
        ))}
      </div>
      <textarea value={detail} onChange={(e) => setDetail(e.target.value)} rows={2}
        placeholder="Optional detail…"
        className="w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
      <div className="flex gap-2">
        <Button type="submit" size="sm">Submit</Button>
        <Button type="button" size="sm" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
      </div>
      {err && <p className="text-sm text-red-500">{err}</p>}
    </form>
  );
}
