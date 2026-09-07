"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import type { PracticalDetail, PracticalSummary } from "@/lib/studyApi";

export function PracticalsClient() {
  const [list, setList] = useState<PracticalSummary[]>([]);
  const [selected, setSelected] = useState<PracticalDetail | null>(null);
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    const query = filter === "all" ? "" : `?subject=${filter}`;
    const r = await fetch(`/api/practicals${query}`).then((x) => x.json()).catch(() => []);
    setList(r);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  async function open(p: PracticalSummary) {
    const r = await fetch(`/api/practicals/${p.id}`).then((x) => x.json()).catch(() => null);
    setSelected(r);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (selected) {
    return (
      <div className="space-y-6">
        <Button variant="secondary" onClick={() => setSelected(null)}>← Back to list</Button>
        <Card className="p-6">
          <Badge color="accent">{selected.subject_slug}</Badge>
          <h2 className="mt-2 text-2xl font-bold">{selected.title}</h2>
          <p className="mt-2 text-ink-2">{selected.objective}</p>

          {selected.requirements && (
            <div className="mt-5">
              <h3 className="text-sm font-semibold text-ink-1">Requirements</h3>
              <p className="mt-1 text-sm text-ink-2">{selected.requirements}</p>
            </div>
          )}
          {selected.principle && (
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-ink-1">Principle</h3>
              <p className="mt-1 text-sm text-ink-2">{selected.principle}</p>
            </div>
          )}

          <div className="mt-6">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">
              Procedure
            </h3>
            <ol className="space-y-3">
              {selected.steps.map((s, i) => (
                <li key={i} className="flex gap-3">
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accent text-xs font-bold text-white">
                    {i + 1}
                  </span>
                  <div>
                    <p className="text-sm text-ink-1">{s.step_text}</p>
                    {s.observation && <p className="text-xs text-ink-3">{s.observation}</p>}
                  </div>
                </li>
              ))}
            </ol>
          </div>

          {(selected.safety_notes || selected.clinical_significance || selected.common_mistakes) && (
            <div className="mt-6 grid gap-3 md:grid-cols-3">
              {selected.safety_notes && <Info title="Safety" text={selected.safety_notes} />}
              {selected.clinical_significance && <Info title="Clinical significance" text={selected.clinical_significance} />}
              {selected.common_mistakes && <Info title="Common mistakes" text={selected.common_mistakes} />}
            </div>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Step 12"
        title="Practicals"
        subtitle="Checklists, step-by-step procedures and spotter guidance for every practical."
      />
      <div className="flex flex-wrap gap-2">
        {["all", "anatomy", "physiology", "biochemistry", "pathology"].map((s) => (
          <button key={s} onClick={() => setFilter(s)}
            className={`rounded-full px-3 py-1 text-sm ${filter === s ? "bg-accent text-white" : "border border-surface-2 text-ink-2"}`}>
            {s === "all" ? "All subjects" : s}
          </button>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {list.map((p) => (
          <button key={p.id} onClick={() => open(p)} className="text-left">
            <Card className="h-full p-5 transition hover:border-accent/40">
              <p className="text-xs uppercase tracking-wider text-ink-3">{p.subject_slug}</p>
              <h3 className="mt-1 font-semibold">{p.title}</h3>
              <p className="mt-1 line-clamp-3 text-sm text-ink-2">{p.objective}</p>
              <span className="mt-3 inline-block text-sm text-accent">Open procedure →</span>
            </Card>
          </button>
        ))}
      </div>
      {list.length === 0 && <p className="text-center text-sm text-ink-2">No practicals for this filter yet.</p>}
    </div>
  );
}

function Info({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-xl border border-surface-2 bg-surface-1 p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">{title}</p>
      <p className="mt-1 text-sm text-ink-2">{text}</p>
    </div>
  );
}
