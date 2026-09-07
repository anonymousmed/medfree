import { API_BASE_URL } from "@medfree/config";
import type { AtlasRegion, AtlasStructure, Subject, TopicBlock, TopicDetail } from "@medfree/types";
import { MOCK_REGIONS, MOCK_STRUCTURES, MOCK_SUBJECTS, MOCK_TOPICS } from "./mock";
import { MOCK_TOPIC_BLOCKS } from "./mockBlocks";

export interface Book {
  id: number;
  title: string;
  edition?: string;
  publisher?: string;
  isbn?: string;
  year?: number;
  subject_slug?: string;
  source_url?: string;
  rights_status?: string;
  license_name?: string;
  author?: { id: number; name: string; affiliation?: string };
  chapters?: { id: number; title: string; chapter_index: number; topic_slug?: string }[];
}

export interface SearchResult {
  type: string;
  id: number;
  title: string;
  subtitle?: string;
  href?: string;
}

export interface Resource {
  id: number;
  title: string;
  resource_type: string;
  creator?: string | null;
  publisher?: string | null;
  source_url?: string | null;
  rights_status: string;
  review_status: string;
  visibility: string;
  local_storage_key?: string | null;
  read_url?: string | null;
}

export const fetchResources = () => get<Resource[]>("/resources", []);

export const fetchResource = (id: number) =>
  get<Resource>(`/resources/${id}`, {
    id, title: "Resource unavailable", resource_type: "unknown",
    rights_status: "unknown", review_status: "unknown", visibility: "private",
  });

export interface ProgressOverview {
  streak: number;
  longest_streak: number;
  xp: number;
  level: number;
  quiz_attempts: number;
  quiz_correct: number;
  quiz_accuracy: number;
  viva_attempts: number;
  topics_started: number;
  topics_completed: number;
  flashcards_due: number;
  time_on_site_seconds: number;
  reading_seconds: number;
  subject_mastery: {
    subject_slug: string;
    attempts: number;
    correct: number;
    accuracy: number;
  }[];
  weak_areas: { topic_slug: string; accuracy?: number | null; mastery?: number | null; note: string }[];
}

export const fetchProgressOverview = () => get<ProgressOverview | null>("/progress/overview", null);

/**
 * Thin API client. Each fetcher first tries the FastAPI backend and falls back
 * to bundled mock data so the UI renders standalone.
 *
 * Base URL selection:
 * - Client (browser): relative "/api" → proxied by Next.js (see next.config).
 * - Server (SSR page data): absolute URL to the backend, because Node fetch
 *   cannot use a relative path.
 */

function base(): string {
  if (typeof window !== "undefined") return API_BASE_URL; // "/api" → proxied by Next
  // Server-side (SSR): MEDFREE_API_URL is the backend origin (no /api suffix),
  // so append the api_v1_prefix to reach the FastAPI routes.
  const origin = process.env.MEDFREE_API_URL ?? "http://127.0.0.1:8000";
  return origin.replace(/\/$/, "") + "/api";
}

async function get<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${base()}${path}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export const fetchSubjects = () => get<Subject[]>("/subjects", MOCK_SUBJECTS);
export const fetchTopics = (subject = "anatomy") =>
  get<TopicDetail[]>(`/subjects/${subject}/topics`, MOCK_TOPICS);
export const fetchTopic = (subject: string, topic: string) =>
  get<TopicDetail>(`/subjects/${subject}/topics/${topic}`, MOCK_TOPICS.find((t) => t.slug === topic) ?? MOCK_TOPICS[0]);

export type TopicNode = {
  slug: string;
  title: string;
  difficulty?: string;
  subject_slug?: string;
};

export const fetchTopicBlocks = (subject: string, topic: string) =>
  get<{
    title: string;
    blocks: TopicBlock[];
    summary?: string;
    mastery?: number;
    difficulty?: string;
    est_minutes?: number;
    prerequisites?: TopicNode[];
    related?: TopicNode[];
    next_topics?: TopicNode[];
  }>(`/subjects/${subject}/topics/${topic}`, MOCK_TOPIC_BLOCKS);

export const fetchBooks = (subject?: string, q?: string) =>
  get<Book[]>(`/books${subject ? `?subject=${subject}` : ""}${q ? `${subject ? "&" : "?"}q=${q}` : ""}`, []);

export const fetchBook = (id: number) => get<Book>(`/books/${id}`, {
  id, title: "Book unavailable", chapters: [],
});

export interface StructureRelation {
  relation_type: string;
  description?: string;
  related_structure: string;
  related_id: number;
  direction: string;
}

export const fetchAtlasSystems = () =>
  get<{ id: number; slug: string; name: string; icon?: string }[]>("/atlas/systems", []);

export const fetchAtlasRelations = (id: number) =>
  get<StructureRelation[]>(`/atlas/structures/${id}/relations`, []);

export const fetchAtlasAnnotations = (id: number) =>
  get<{ id: number; label: string; description?: string }[]>(`/atlas/structures/${id}/annotations`, []);

export const fetchAtlasRegions = () => get<AtlasRegion[]>("/atlas/regions", MOCK_REGIONS);
export const fetchAtlasStructures = (region?: string) =>
  get<AtlasStructure[]>(`/atlas/structures${region ? `?region=${region}` : ""}`, MOCK_STRUCTURES);
