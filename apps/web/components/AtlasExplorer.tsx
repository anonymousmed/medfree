"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import type { AtlasRegion, AtlasStructure } from "@medfree/types";
import {
  fetchAtlasRegions,
  fetchAtlasStructures,
  fetchAtlasRelations,
  fetchAtlasAnnotations,
  type StructureRelation,
} from "@/lib/api";
import { Badge, Button } from "@medfree/ui";

const AtlasViewer = dynamic(
  () => import("@medfree/atlas").then((m) => m.AtlasViewer),
  { ssr: false }
);

export function AtlasExplorer({
  systems = [],
}: {
  systems?: { id: number; slug: string; name: string }[];
}) {
  const [regions, setRegions] = useState<AtlasRegion[]>([]);
  const [activeRegion, setActiveRegion] = useState<string>("upper-limb");
  const [structures, setStructures] = useState<AtlasStructure[]>([]);
  const [selected, setSelected] = useState<AtlasStructure | null>(null);
  const [relations, setRelations] = useState<StructureRelation[]>([]);
  const [annotations, setAnnotations] = useState<{ id: number; label: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAtlasRegions().then((r) => setRegions(r));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchAtlasStructures(activeRegion).then((s) => {
      setStructures(s);
      setSelected(s[0] ?? null);
      setLoading(false);
    });
  }, [activeRegion]);

  useEffect(() => {
    if (!selected) return;
    fetchAtlasRelations(selected.id).then(setRelations);
    fetchAtlasAnnotations(selected.id).then(setAnnotations);
  }, [selected?.id]);

  const parts = structures.map((s) => ({
    id: String(s.id),
    name: s.preferred_name,
    label: s.preferred_name,
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
      {/* Viewer (primary, large) */}
      <div className="rounded-2xl border border-surface-2 bg-surface-1 p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-ink-3">Region</span>
          {regions.map((r) => (
            <button key={r.slug} onClick={() => setActiveRegion(r.slug)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                r.slug === activeRegion ? "bg-accent text-white" : "bg-surface-2 text-ink-2 hover:bg-surface-3"
              }`}>
              {r.name}
            </button>
          ))}
        </div>

        {/* System / layer controls */}
        {systems.length > 0 && (
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-3">Systems</span>
            {systems.map((s) => (
              <Badge key={s.id} color="neutral">{s.name}</Badge>
            ))}
          </div>
        )}

        {loading ? (
          <div className="grid aspect-video w-full place-items-center rounded-xl bg-surface-2 text-sm text-ink-3">
            Loading 3D scene…
          </div>
        ) : (
          <AtlasViewer parts={parts} activePartId={selected ? String(selected.id) : null} />
        )}

        <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink-3">
          <Badge color="neutral">Rotate</Badge>
          <Badge color="neutral">Zoom</Badge>
          <Badge color="neutral">Pan</Badge>
          <Badge color="neutral">Isolate</Badge>
          <Badge color="neutral">Hide/Show</Badge>
          <Badge color="neutral">Highlight</Badge>
          <Badge color="neutral">Labels</Badge>
        </div>
      </div>

      {/* Structure information panel */}
      <div className="rounded-2xl border border-surface-2 bg-surface-1 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Structures</p>
        <div className="mt-2 max-h-44 overflow-auto rounded-xl bg-surface-2/50 p-1">
          {structures.map((s) => (
            <button key={s.id} onClick={() => setSelected(s)}
              className={`block w-full rounded-lg px-3 py-2 text-left text-sm ${
                selected?.id === s.id ? "bg-accent-soft/20 text-accent" : "text-ink-2 hover:bg-surface-2"
              }`}>
              {s.preferred_name}
            </button>
          ))}
        </div>

        {selected && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-lg font-semibold">{selected.preferred_name}</p>
              <Badge color="success">Verified</Badge>
            </div>
            {selected.latin_name && <p className="text-xs italic text-ink-3">{selected.latin_name}</p>}
            <p className="text-sm text-ink-2">{selected.description}</p>
            {selected.clinical_notes && (
              <div className="rounded-xl border border-accent/25 bg-accent-soft/10 p-3">
                <p className="text-xs font-semibold text-accent">CLINICAL RELEVANCE</p>
                <p className="mt-1 text-sm text-ink-2">{selected.clinical_notes}</p>
              </div>
            )}

            {relations.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-ink-3">Relations</p>
                <ul className="space-y-1">
                  {relations.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 rounded-lg bg-surface-2/50 px-2 py-1.5 text-xs">
                      <span className="text-ink-3">{r.relation_type} →</span>
                      <span className="font-medium">{r.related_structure}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {annotations.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-ink-3">Pins / labels</p>
                <ul className="space-y-1">
                  {annotations.map((a) => (
                    <li key={a.id} className="rounded-lg bg-surface-2/50 px-2 py-1.5 text-xs"><span className="text-accent">📍</span> {a.label}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button size="sm">MCQs</Button>
              <Button size="sm" variant="secondary">Viva</Button>
              <Button size="sm" variant="secondary">Flashcards</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
