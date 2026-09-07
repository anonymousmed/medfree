"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";

type Profile = {
  id: number;
  email?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  course?: string | null;
  year_of_study?: string | null;
  university?: string | null;
  country?: string | null;
  preferred_language?: string | null;
  study_goal?: string | null;
  highest_role: string;
};

export function ProfileEditor() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [profile, setProfile] = useState<Profile | null>(null);
  const [form, setForm] = useState<Partial<Profile>>({});
  const [saved, setSaved] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch("/api/me/profile", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Sign in to view your profile.");
      const data: Profile = await res.json();
      setProfile(data);
      setForm(data);
    } catch (e: any) {
      setError(e?.message ?? null);
    }
  }, [token]);

  useEffect(() => { if (token) load(); }, [load, token]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/me/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(form),
    });
    if (res.ok) { setSaved(true); load(); setTimeout(() => setSaved(false), 2000); }
    else { const b = await res.json(); setError(b?.detail ?? "Save failed"); }
  }

  if (error) {
    return (
      <Card className="p-6 text-center text-ink-2">
        <p>{error}</p>
        <p className="mt-1 text-sm text-ink-3">Profile is per-account; sign in to edit it.</p>
      </Card>
    );
  }
  if (!profile) return <Card className="p-6 text-center text-sm text-ink-2">Loading…</Card>;

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Account"
        title="Your profile"
        subtitle="Course and study details help personalise your learning. Everything is optional."
      />

      <div className="flex items-center gap-4">
        <span className="grid h-16 w-16 place-items-center rounded-2xl bg-accent text-2xl font-bold text-white">
          {(profile.display_name || "S")[0].toUpperCase()}
        </span>
        <div>
          <p className="text-lg font-semibold">{profile.display_name || "You"}</p>
          <p className="text-sm text-ink-3">{profile.email}</p>
          <Badge color="accent">{profile.highest_role}</Badge>
        </div>
      </div>

      <form onSubmit={save} className="grid gap-4 sm:grid-cols-2">
        <Field label="Display name" value={form.display_name ?? ""} onChange={(v) => set("display_name", v)} />
        <Field label="Course" value={form.course ?? ""} onChange={(v) => set("course", v)} placeholder="MBBS" />
        <Field label="Year of study" value={form.year_of_study ?? ""} onChange={(v) => set("year_of_study", v)} placeholder="1" />
        <Field label="University" value={form.university ?? ""} onChange={(v) => set("university", v)} placeholder="e.g. AIIMS" />
        <Field label="Country" value={form.country ?? ""} onChange={(v) => set("country", v)} placeholder="IN" />
        <Field label="Preferred language" value={form.preferred_language ?? ""} onChange={(v) => set("preferred_language", v)} placeholder="en" />
        <div className="sm:col-span-2">
          <label className="block">
            <span className="text-xs font-medium text-ink-3">Study goal</span>
            <textarea
              value={form.study_goal ?? ""}
              onChange={(e) => set("study_goal", e.target.value)}
              rows={3}
              placeholder="e.g. Pass first-year exams with strong anatomy fundamentals."
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none"
            />
          </label>
        </div>
        <div className="sm:col-span-2 flex items-center gap-3">
          <Button type="submit">Save profile</Button>
          {saved && <span className="text-sm text-accent">Saved ✓</span>}
        </div>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-ink-3">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none"
      />
    </label>
  );
}
