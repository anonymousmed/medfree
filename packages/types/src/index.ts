/**
 * @medfree/types — shared TS types used by the web app and UI packages.
 * These mirror the backend SQLAlchemy/Pydantic models (see apps/api/app/models).
 */

export type Role =
  | "student"
  | "contributor"
  | "reviewer"
  | "medical_reviewer"
  | "moderator"
  | "content_admin"
  | "super_admin";

export interface UserProfile {
  id: number;
  email?: string;
  display_name?: string;
  avatar_url?: string;
  highest_role: Role;
}

export interface Subject {
  id: number;
  slug: string;
  title: string;
  description?: string;
  icon?: string;
  color?: string;
}

export interface TopicSummary {
  id: number;
  slug: string;
  title: string;
  summary?: string;
  mastery?: number;
}

export interface TopicDetail extends TopicSummary {
  content_markdown?: string;
  learning_objectives?: string;
}

export type TopicBlockType =
  | "overview"
  | "objectives"
  | "atlas"
  | "diagram"
  | "clinical"
  | "mcq"
  | "viva"
  | "flashcard"
  | "practical"
  | "books"
  | "revision";

export interface TopicBlock {
  id: number;
  position: number;
  block_type: TopicBlockType;
  title: string;
  content?: string;
  meta?: string;
}

export interface TopicDetailWithBlocks extends TopicSummary {
  learning_objectives?: string;
  blocks: TopicBlock[];
}

export interface AtlasRegion {
  id: number;
  slug: string;
  name: string;
  parent_id?: number;
}

export interface AtlasStructure {
  id: number;
  preferred_name: string;
  latin_name?: string;
  synonyms?: string;
  region_id?: number;
  system_id?: number;
  description?: string;
  clinical_notes?: string;
}

export interface AtlasSearchResult {
  id: number;
  preferred_name: string;
  region_slug?: string;
  type: string;
}

export interface Resource {
  id: number;
  title: string;
  resource_type: string;
  creator?: string;
  publisher?: string;
  source_url?: string;
  rights_status: string;
  ai_usage_status: string;
  review_status: string;
  visibility: string;
}

export interface LearningFlowStep {
  key: string;
  label: string;
  kind: "overview" | "visual" | "atlas" | "clinical" | "practice" | "mcq" | "viva" | "flashcard" | "books" | "revision";
}
