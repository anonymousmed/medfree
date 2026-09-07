"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, ProgressBar, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";
import type { Flashcard, FlashcardStats, FlashcardReviewResult } from "@/lib/studyApi";

type Mode = "review" | "browse";

const SUBJECTS = ["anatomy", "physiology", "biochemistry"];

export function FlashcardsClient() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [subject, setSubject] = useState("anatomy");
  const [mode, setMode] = useState<Mode>("review");
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [due, setDue] = useState<Flashcard[]>([]);
  const [stats, setStats] = useState<FlashcardStats | null>(null);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [reviewed, setReviewed] = useState<FlashcardReviewResult | null>(null);

  const load = useCallback(async () => {
    const [c, d, s] = await Promise.all([
      fetch(`/api/flashcards?subject=${subject}`).then((r) => r.json()).catch(() => []),
      fetch(`/api/flashcards/due?subject=${subject}`).then((r) => r.json()).catch(() => []),
      fetch(`/api/flashcards/stats`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.json()).catch(() => null),
    ]);
    setCards(c);
    setDue(d);
    setStats(s);
    setIndex(0);
    setFlipped(false);
  }, [subject, token]);

  useEffect(() => { load(); }, [load]);

  const deck = mode === "review" && due.length ? due : cards;
  const current = deck[index];
  const accuracy = useMemo(() => {
    if (!stats || !stats.reviewed) return 0;
    return Math.round((stats.reviewed / Math.max(stats.total_cards, 1)) * 100);
  }, [stats]);

  async function rate(quality: number) {
    if (!current) return;
    try {
      const res = await fetch(`/api/flashcards/${current.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ quality }),
      });
      const data: FlashcardReviewResult = await res.json();
      setReviewed(data);
      setFlipped(false);
      setIndex((i) => i + 1);
      setNotice(`Interval scheduled: ${data.interval_days} day(s).`);
      load();
    } catch {
      setNotice("Could not save the review — check your connection or sign in.");
    }
  }

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Step 11"
        title="Flashcards"
        subtitle="Spaced repetition over every topic. Grade each card, and the schedule adapts."
      />

      <div className="flex flex-wrap items-center gap-2">
        {SUBJECTS.map((s) => (
          <button key={s} onClick={() => setSubject(s)}
            className={`rounded-full px-3 py-1 text-sm ${subject === s ? "bg-accent text-white" : "border border-surface-2 text-ink-2"}`}>
            {s}
          </button>
        ))}
        <span className="mx-1 h-5 w-px bg-surface-2" />
        <Button size="sm" variant={mode === "review" ? "primary" : "secondary"} onClick={() => setMode("review")}>
          Review due ({due.length})
        </Button>
        <Button size="sm" variant={mode === "browse" ? "primary" : "secondary"} onClick={() => setMode("browse")}>
          Browse all ({cards.length})
        </Button>
      </div>

      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Total cards", stats.total_cards],
            ["Due now", stats.due_now],
            ["Reviewed", stats.reviewed],
            ["Avg interval", `${stats.average_interval_days}d`],
          ].map(([label, value]) => (
            <Card key={label as string} className="p-4">
              <p className="text-xs uppercase tracking-wider text-ink-3">{label}</p>
              <p className="mt-1 text-2xl font-bold">{value}</p>
            </Card>
          ))}
        </div>
      )}

      <Card className="p-6">
        {current ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm text-ink-3">
              <span>Card {index + 1} / {deck.length}</span>
              <span className="rounded bg-surface-2 px-2 py-0.5 text-xs">{current.card_type}</span>
            </div>

            <button onClick={() => setFlipped((f) => !f)}
              className="block min-h-[8rem] w-full rounded-2xl border border-surface-2 bg-surface-1 p-6 text-left text-lg leading-relaxed">
              {flipped ? current.back : current.front}
            </button>
            {!flipped && <p className="text-center text-xs text-ink-3">Tap to reveal the answer</p>}

            {flipped && mode === "review" && (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                {["Again", "Hard", "Good", "Easy", "Perfect"].map((label, i) => (
                  <Button key={label} variant={i < 2 ? "secondary" : "primary"} onClick={() => rate(QUALITY[i])}>
                    {label}
                  </Button>
                ))}
              </div>
            )}

            {notice && <p className="text-sm text-ink-2">{notice}</p>}
            {mode === "review" && due.length === 0 && (
              <p className="text-center text-sm text-accent">All caught up — no cards due right now.</p>
            )}
          </div>
        ) : (
          <p className="text-center text-sm text-ink-2">No cards found for this subject. Try another subject or browse all.</p>
        )}
      </Card>
    </div>
  );
}

const QUALITY = [1, 3, 4, 5, 5];
