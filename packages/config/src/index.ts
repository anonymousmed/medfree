/** @medfree/config — shared app config & constants. */

export const APP_NAME = "MEDFREE";
export const PRODUCT_TAGLINE =
  "A free, tablet/desktop-first digital medical university with full phone compatibility.";

/**
 * API base URL used by the web app.
 * - In dev/live preview this is relative ("/api") so Next.js proxies it to the
 *   FastAPI backend (see next.config.mjs rewrite).
 * - In production set NEXT_PUBLIC_API_URL to the hosted backend (Render/Railway).
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

/** Homepage / dashboard priority order (mandate #12). */
export const HOME_PRIORITY = [
  "continue",
  "atlas",
  "subjects",
  "topics",
  "practice",
  "clinical",
  "books",
  "progress",
] as const;

/** The canonical learning flow (mandate #3). */
export const LEARNING_FLOW = [
  { key: "overview", label: "Quick Explanation" },
  { key: "visual", label: "Visual Learning" },
  { key: "atlas", label: "Human Atlas / 3D" },
  { key: "diagram", label: "Interactive Diagram" },
  { key: "clinical", label: "Clinical Correlation" },
  { key: "practical", label: "Practical Learning" },
  { key: "mcq", label: "MCQs" },
  { key: "viva", label: "Viva" },
  { key: "flashcards", label: "Flashcards" },
  { key: "books", label: "Books & Research" },
  { key: "revision", label: "Revision" },
  { key: "mastery", label: "Mastery Tracking" },
] as const;

export interface NavItem {
  href: string;
  label: string;
  icon: string;
  featured?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", icon: "home" },
  { href: "/atlas", label: "Atlas", icon: "atlas", featured: true },
  { href: "/learn", label: "Learn", icon: "learn" },
  { href: "/practice", label: "Practice", icon: "practice" },
  { href: "/flashcards", label: "Flashcards", icon: "practice" },
  { href: "/practicals", label: "Practicals", icon: "practice" },
  { href: "/assistant", label: "Assistant", icon: "search" },
  { href: "/library", label: "Library", icon: "library" },
  { href: "/progress", label: "Progress", icon: "progress" },
  { href: "/gamification", label: "Rewards", icon: "progress" },
  { href: "/partners", label: "Partners", icon: "progress" },
  { href: "/profile", label: "Profile", icon: "progress" },
  { href: "/admin", label: "Admin", icon: "progress" },
];
