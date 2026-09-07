"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Card, ProgressBar, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";
import type { ProgressOverview } from "@/lib/api";

const SUBJECT_LABELS: Record<string, string> = {
  anatomy: "Anatomy",
  physiology: "Physiology",
  biochemistry: "Biochemistry",
};

function fmtDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `${mins} min`;
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  return rem ? `${hrs}h ${rem}m` : `${hrs}h`;
}

export function ProgressClient() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [data, setData] = useState<ProgressOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) {
      setError("Sign in to see your progress.");
      setLoading(false);
      return;
    }
    try {
      const res = await fetch("/api/progress/overview", {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (!res.ok) throw new Error("Could not load progress");
      setData(await res.json());
      setError(null);
    } catch (e: any) {
      setError(e?.message ?? "Could not load progress");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  // Auto-refresh every 30s so the dashboard feels live.
  useEffect(() => {
    if (!token) return;
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [load, token]);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6">
        <SectionHeading eyebrow="Progress" title="Mastery & Analytics" subtitle="Real data from your study activity." />
        <Card className="p-6 text-sm text-ink-3">Loading your progress…</Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-6xl space-y-6">
        <SectionHeading eyebrow="Progress" title="Mastery & Analytics" subtitle="Real data from your study activity." />
        <Card className="p-6 text-center text-sm text-ink-2">{error ?? "No progress data yet."}</Card>
      </div>
    );
  }

  const hasActivity =
    data.quiz_attempts > 0 || data.viva_attempts > 0 || data.topics_completed > 0 ||
    data.time_on_site_seconds > 0 || data.reading_seconds > 0 || data.streak > 0;

  const cardData = [
    ["Day streak", `${data.streak}`, `${data.streak === 1 ? "day" : "days"} in a row`],
    ["Questions solved", `${data.quiz_correct}`, `of ${data.quiz_attempts} attempted`],
    ["Viva done", `${data.viva_attempts}`, "practised aloud"],
    ["Time on site", fmtDuration(data.time_on_site_seconds), "measured while you study"],
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionHeading
        eyebrow="Progress"
        title="Mastery & Analytics"
        subtitle="Personalised from your real study data — time on site, questions solved, books read and streaks."
      />

      {!hasActivity && (
        <Card className="border-accent/30 bg-accent-soft/10 p-5">
          <p className="text-sm text-ink-2">
            <span className="font-semibold text-accent">Welcome!</span> Your progress is
            currently empty because you haven&apos;t studied on MEDFREE yet. Start a quiz, do a
            viva, open a topic or read a book and it will appear here — tracked automatically, no
            fake numbers.
          </p>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cardData.map(([label, value, sub]) => (
          <Card key={label}>
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">{label}</p>
            <p className="mt-1 text-3xl font-bold">{value}</p>
            <p className="mt-1 text-xs text-ink-3">{sub}</p>
          </Card>
        ))}
      </div>

      {/* XP / level */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <p className="font-semibold">Level {data.level}</p>
            <Badge color="accent">{data.xp} XP</Badge>
          </div>
          <div className="mt-3">
            <ProgressBar value={data.xp % 100} label={`Level ${data.level} → ${data.level + 1}`} />
          </div>
          <p className="mt-2 text-xs text-ink-3">{100 - (data.xp % 100)} XP to the next level.</p>
        </Card>

        <Card className="p-5">
          <p className="mb-3 font-semibold">Reading & review</p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-ink-3">Minutes read books</p>
              <p className="mt-1 text-2xl font-bold">{Math.round(data.reading_seconds / 60)}</p>
            </div>
            <div>
              <p className="text-xs text-ink-3">Flashcards due</p>
              <p className="mt-1 text-2xl font-bold">{data.flashcards_due}</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <p className="mb-3 font-semibold">Subject mastery</p>
          {data.subject_mastery.length === 0 ? (
            <p className="text-sm text-ink-3">No subject data yet — answer some MCQs first.</p>
          ) : (
            <div className="space-y-3">
              {data.subject_mastery.map((s) => (
                <ProgressBar
                  key={s.subject_slug}
                  value={s.accuracy}
                  label={`${SUBJECT_LABELS[s.subject_slug] ?? s.subject_slug} — ${s.correct}/${s.attempts} correct`}
                />
              ))}
            </div>
          )}
        </Card>

        <Card className="p-5">
          <p className="mb-3 font-semibold">Weak areas</p>
          {data.weak_areas.length === 0 ? (
            <p className="text-sm text-ink-3">Nothing flagged yet — keep studying and low-scoring topics will appear here.</p>
          ) : (
            <div className="space-y-2 text-sm text-ink-2">
              {data.weak_areas.map((w) => (
                <p key={w.topic_slug} className="rounded-lg bg-surface-2/50 px-3 py-2">
                  {w.topic_slug.replace(/-/g, " ")}
                  {w.accuracy != null && <span className="text-ink-3"> — {w.accuracy}%</span>}
                  {w.mastery != null && <span className="text-ink-3"> — mastery {w.mastery}%</span>}
                  <span className="ml-2 text-accent">→ {w.note}</span>
                </p>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
