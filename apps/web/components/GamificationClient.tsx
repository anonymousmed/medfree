"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Card, ProgressBar, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";
import type { GamificationSummary } from "@/lib/studyApi";

const BADGE_META: Record<string, { icon: string }> = {
  first_topic: { icon: "🎯" },
  viva_starter: { icon: "🗣️" },
  first_revision: { icon: "🔁" },
  mcq_100: { icon: "✔️" },
  mcq_500: { icon: "🏆" },
  streak_7: { icon: "🔥" },
  streak_30: { icon: "⚡" },
  subject_master: { icon: "🎓" },
};

export function GamificationClient() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [data, setData] = useState<GamificationSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch("/api/gamification/summary", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Sign in to see your progress");
      setData(await res.json());
    } catch (e: any) {
      setError(e?.message ?? null);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  if (error) {
    return (
      <Card className="p-6 text-center">
        <p className="text-ink-2">{error}</p>
        <p className="mt-2 text-sm text-ink-3">Progress, streaks and badges are tracked per account.</p>
      </Card>
    );
  }
  if (!data) return <Card className="p-6 text-center text-sm text-ink-2">Loading your progress…</Card>;

  const xpIntoLevel = data.xp % 100;
  const quizCorrect = Math.round(data.quiz_attempts * (data.quiz_accuracy / 100));

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Step 14"
        title="Your Learning Rewards"
        subtitle="Earn XP and badges from real study activity — quizzes, viva, flashcards and completed topics."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Day streak" value={data.streak.current} suffix="days" subtitle={`Longest: ${data.streak.longest}`} />
        <Stat label="Total XP" value={data.xp} />
        <Stat label="Level" value={data.level} />
        <Stat label="Topics completed" value={data.topics_completed} />
      </div>

      <Card className="p-5">
        <ProgressBar value={xpIntoLevel} label={`Level ${data.level} → ${data.level + 1}`} />
        <p className="mt-2 text-xs text-ink-3">{100 - xpIntoLevel} XP to the next level.</p>
      </Card>

      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Badges</h3>
        {data.badges.length === 0 ? (
          <Card className="p-4 text-sm text-ink-2">No badges yet — complete your first activity to unlock one.</Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {data.badges.map((b) => (
              <Card key={b.key} className="p-4">
                <span className="text-2xl">{BADGE_META[b.key]?.icon ?? "🏅"}</span>
                <p className="mt-2 text-sm font-semibold">{b.title}</p>
                <p className="mt-0.5 text-xs text-ink-3">{b.description}</p>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MiniStat label="Quiz attempts" value={data.quiz_attempts} />
        <MiniStat label="Quiz accuracy" value={`${data.quiz_accuracy}%`} />
        <MiniStat label="Topics completed" value={data.topics_completed} />
        <MiniStat label="MCQs correct" value={quizCorrect} />
      </div>
    </div>
  );
}

function Stat({ label, value, suffix, subtitle }: { label: string; value: number; suffix?: string; subtitle?: string }) {
  return (
    <Card className="p-5">
      <p className="text-xs uppercase tracking-wider text-ink-3">{label}</p>
      <p className="mt-1 text-3xl font-bold">
        {value}
        {suffix && <span className="ml-1 text-sm font-normal text-ink-3">{suffix}</span>}
      </p>
      {subtitle && <p className="mt-0.5 text-xs text-ink-3">{subtitle}</p>}
    </Card>
  );
}

function MiniStat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-surface-2 bg-surface-1 p-3 text-center">
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs text-ink-3">{label}</p>
    </div>
  );
}
