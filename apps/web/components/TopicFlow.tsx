"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge, Button, Card, ProgressBar } from "@medfree/ui";
import type { TopicBlock } from "@medfree/types";
import { useAuth } from "./AuthProvider";
import { authedFetch } from "@/lib/clientApi";

const BLOCK_ICONS: Record<string, string> = {
  overview: "🧭",
  objectives: "🎯",
  atlas: "🧠",
  diagram: "🖼️",
  clinical: "🫀",
  mcq: "❓",
  viva: "🗣️",
  flashcard: "🃏",
  practical: "🧪",
  books: "📚",
  revision: "🔁",
};

const BLOCK_LABEL: Record<string, string> = {
  overview: "What is it",
  objectives: "Learning objectives",
  atlas: "Human Atlas",
  diagram: "Interactive",
  clinical: "Clinical",
  mcq: "MCQs",
  viva: "Viva",
  flashcard: "Flashcards",
  practical: "Practical",
  books: "Books & research",
  revision: "Revision",
};

export function TopicFlow({
  subjectSlug,
  topicSlug,
  blocks,
  initialMastery = 0,
}: {
  subjectSlug: string;
  topicSlug: string;
  blocks: TopicBlock[];
  initialMastery?: number;
}) {
  const [mastery, setMastery] = useState(initialMastery);
  const [bookmarked, setBookmarked] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const { session } = useAuth();
  const token = session?.access_token;

  async function markComplete() {
    if (!token) {
      setMessage("Sign in to track progress.");
      return;
    }
    try {
      await authedFetch("/api/progress/topics", {
        method: "POST",
        body: JSON.stringify({ subject_slug: subjectSlug, topic_slug: topicSlug, state: "completed", mastery: 100 }),
      }, token);
      setMastery(100);
      setMessage("Topic marked complete ✓");
    } catch (e) {
      setMessage("Could not save progress.");
    }
  }

  async function toggleBookmark() {
    setBookmarked((b) => !b);
    if (!token) {
      setMessage("Sign in to bookmark.");
      return;
    }
    try {
      await authedFetch("/api/me/bookmarks", {
        method: "POST",
        body: JSON.stringify({ target_type: "topic", target_slug: topicSlug, title: topicSlug }),
      }, token);
      setMessage("Bookmark saved ✓");
    } catch {
      setBookmarked((b) => !b);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="bg-surface-2/40">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <ProgressBar value={mastery} label="Mastery" className="max-w-xs" />
          <div className="flex gap-2">
            <Button size="sm" onClick={toggleBookmark}>{bookmarked ? "✓ Bookmarked" : "Bookmark"}</Button>
            <Button size="sm" variant="primary" onClick={markComplete}>Mark complete</Button>
          </div>
        </div>
        {message && <p className="mt-2 text-xs text-accent">{message}</p>}
      </Card>

      {blocks.map((b) => (
        <Card key={b.id} className="border-l-4" style={{ borderLeftColor: "rgb(var(--accent))" }}>
          <div className="flex items-center gap-3">
            <span className="text-xl">{BLOCK_ICONS[b.block_type] ?? "📌"}</span>
            <div>
              <p className="text-xs uppercase tracking-wider text-ink-3">{BLOCK_LABEL[b.block_type] ?? b.block_type}</p>
              <h3 className="text-lg font-semibold">{b.title}</h3>
            </div>
          </div>
          <div className="mt-3">
            <BlockContent block={b} />
          </div>
        </Card>
      ))}
    </div>
  );
}

function BlockContent({ block }: { block: TopicBlock }) {
  // Preserve newlines in text content (objectives etc.).
  let meta: Record<string, string> = {};
  if (block.meta) {
    try { meta = JSON.parse(block.meta); } catch { /* ignore */ }
  }
  switch (block.block_type) {
    case "atlas":
      return (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-surface-2/50 p-4">
          <p className="text-sm text-ink-2">{block.content}</p>
          <Link href="/atlas" className="inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-semibold text-white">
            Open Atlas →
          </Link>
        </div>
      );
    case "mcq":
    case "viva":
    case "flashcard":
    case "practical":
      return (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-surface-2/50 p-4">
          <p className="text-sm text-ink-2">{block.content}</p>
          <Link href="/practice" className="rounded-lg bg-surface-2 px-3 py-2 text-sm font-medium hover:bg-surface-3">
            Go to practice →
          </Link>
        </div>
      );
    case "books":
      return (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-surface-2/50 p-4">
          <p className="text-sm text-ink-2">{block.content}</p>
          <Link href="/library" className="rounded-lg bg-surface-2 px-3 py-2 text-sm font-medium hover:bg-surface-3">
            Library →
          </Link>
        </div>
      );
    default:
      return <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-2">{block.content}</p>;
  }
}
