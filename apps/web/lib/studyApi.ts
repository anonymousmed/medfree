"use client";

/** Typed helpers for the Study phase features (Steps 11–15). */

export interface Flashcard {
  id: number;
  subject_slug: string;
  topic_slug?: string | null;
  front: string;
  back: string;
  card_type: string;
}

export interface FlashcardStats {
  total_cards: number;
  due_now: number;
  reviewed: number;
  average_interval_days: number;
}

export interface FlashcardReviewResult {
  id: number;
  quality: number;
  interval_days: number;
  due_at: string;
}

export interface PracticalStep {
  position: number;
  step_text: string;
  observation?: string | null;
}

export interface PracticalSummary {
  id: number;
  title: string;
  subject_slug: string;
  objective: string;
}

export interface PracticalDetail extends PracticalSummary {
  topic_slug?: string | null;
  requirements?: string | null;
  principle: string;
  preparation?: string | null;
  observation?: string | null;
  interpretation?: string | null;
  common_mistakes?: string | null;
  safety_notes?: string | null;
  clinical_significance?: string | null;
  reference_text?: string | null;
  steps: PracticalStep[];
}

export interface AiSource {
  source_type: string;
  source_id: number | null;
  title: string;
  href?: string | null;
}

export interface AiAnswer {
  answer: string;
  sources: AiSource[];
  disclaimer: string;
}

export interface GamificationStat {
  current: number;
  longest: number;
}

export interface GamificationSummary {
  streak: GamificationStat;
  xp: number;
  level: number;
  quiz_attempts: number;
  quiz_accuracy: number;
  topics_completed: number;
  badges: { key: string; title: string; description: string; earned_at: string }[];
}

export interface Announcement {
  id: number;
  kind: string;
  title: string;
  body: string | null;
  link: string | null;
}

export interface Ad {
  id: number;
  title: string | null;
  image_key: string | null;
  target_url: string | null;
  alt_text: string | null;
  placement: string;
}

export async function fetchJson<T>(path: string, token?: string | null): Promise<T> {
  const res = await fetch(path, {
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function postJson<T>(path: string, body: unknown, token?: string | null): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const b = await res.text().catch(() => "");
    throw new Error(`${res.status}: ${b}`);
  }
  return (await res.json()) as T;
}
