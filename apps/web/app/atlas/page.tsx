import type { Metadata } from "next";
import Link from "next/link";
import { AtlasExplorer } from "@/components/AtlasExplorer";
import { SectionHeading } from "@medfree/ui";
import { fetchAtlasSystems } from "@/lib/api";

export const metadata: Metadata = { title: "Human Atlas" };

export default async function AtlasPage() {
  const systems = await fetchAtlasSystems();
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionHeading
        eyebrow="Centerpiece"
        title="Human Atlas"
        subtitle="Interactive 3D anatomy, structure identification, clinical correlation, quiz, viva and flashcards — all wired to every topic."
      />
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-ink-2/15 bg-bg-2/40 p-4">
        <p className="text-sm text-ink-2">
          Go deeper with the <strong className="text-ink-1">Detailed Human Atlas</strong> — 2,234
          selectable meshes, system layers, search &amp; exploded views.
        </p>
        <Link
          href="/detailed-atlas"
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
        >
          Detailed Atlas →
        </Link>
      </div>
      <AtlasExplorer systems={systems} />
    </div>
  );
}
