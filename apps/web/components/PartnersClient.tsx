"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Card, SectionHeading } from "@medfree/ui";

type Partner = {
  id: number;
  name: string;
  kind: string;
  country?: string | null;
  region?: string | null;
  website?: string | null;
  description?: string | null;
  is_featured: boolean;
};

export function PartnersClient() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [form, setForm] = useState({
    organization_type: "medical_college",
    organization_name: "",
    contact_name: "",
    contact_email: "",
    goal: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState<string | null>(null);

  const load = useCallback(async () => {
    const r = await fetch("/api/partners").then((x) => x.json()).catch(() => []);
    setPartners(r);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/partners/interest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    setSubmitted(data.message ?? "Thanks for reaching out!");
  }

  const kinds: Record<string, string> = {
    medical_college: "Medical college",
    university: "University",
    research_institute: "Research institute",
    student_group: "Student group",
    faculty: "Faculty",
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <SectionHeading
        eyebrow="Step 20 · Partnerships"
        title="Partners & Institutions"
        subtitle="MEDFREE collaborates with medical colleges, faculty and student groups to build and review curriculum content."
      />

      {submitted ? (
        <Card className="p-6 text-center">
          <p className="text-2xl">✅</p>
          <p className="mt-2 font-semibold">{submitted}</p>
          <p className="text-sm text-ink-3">We'll review your interest and get back to you.</p>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="p-6">
            <h3 className="text-lg font-semibold">Become a partner</h3>
            <p className="mt-1 text-sm text-ink-2">
              Colleges, faculty and student groups can collaborate on content review, research and outreach.
            </p>
            <form onSubmit={submit} className="mt-4 space-y-3">
              <Field label="Organization type">
                <select value={form.organization_type} onChange={(e) => setForm({ ...form, organization_type: e.target.value })}
                  className="w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none">
                  {Object.entries(kinds).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </Field>
              <Field label="Organization name">
                <input required value={form.organization_name} onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
                  className="w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
              </Field>
              <Field label="Contact name">
                <input required value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
                  className="w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
              </Field>
              <Field label="Contact email">
                <input type="email" required value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                  className="w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
              </Field>
              <Field label="Goal (optional)">
                <input value={form.goal} onChange={(e) => setForm({ ...form, goal: e.target.value })}
                  className="w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
              </Field>
              <Field label="Message (optional)">
                <textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })}
                  rows={3} className="w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
              </Field>
              <button type="submit" className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:brightness-110">
                Submit interest
              </button>
            </form>
          </Card>

          <Card className="p-4">
            <h3 className="mb-3 text-lg font-semibold">Partner directory</h3>
            {partners.length === 0 ? (
              <p className="text-sm text-ink-3">Partner institutions will appear here as they join.</p>
            ) : (
              <div className="space-y-3">
                {partners.map((p) => (
                  <div key={p.id} className="rounded-xl bg-surface-2/40 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold">{p.name}</p>
                      <Badge color={p.is_featured ? "accent" : "neutral"}>{kinds[p.kind] ?? p.kind}</Badge>
                    </div>
                    {(p.country || p.region) && <p className="mt-1 text-xs text-ink-3">{[p.region, p.country].filter(Boolean).join(" · ")}</p>}
                    {p.description && <p className="mt-1 text-sm text-ink-2">{p.description}</p>}
                    {p.website && <a href={p.website} target="_blank" rel="noreferrer" className="mt-1 inline-block text-sm text-accent hover:underline">Visit site ↗</a>}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-ink-3">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
