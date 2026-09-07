"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";

type Institution = {
  id: number;
  name: string;
  kind: string;
  country?: string | null;
  website?: string | null;
  is_featured: boolean;
  is_active: boolean;
};

type Request = {
  id: number;
  organization_type: string;
  organization_name: string;
  contact_name: string;
  contact_email: string;
  goal?: string | null;
  message?: string | null;
  status: string;
};

export function AdminPartners() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [partners, setPartners] = useState<Institution[]>([]);
  const [requests, setRequests] = useState<Request[]>([]);
  const [name, setName] = useState("");
  const [kind, setKind] = useState("medical_college");
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    const h = { Authorization: `Bearer ${token}` };
    const [p, r] = await Promise.all([
      fetch("/api/admin/partners", { headers: h }).then((x) => x.json()),
      fetch("/api/admin/partnership-requests", { headers: h }).then((x) => x.json()),
    ]);
    setPartners(p);
    setRequests(r);
  }, [token]);

  useEffect(() => { if (token) load(); }, [load, token]);

  async function createPartner() {
    const res = await fetch("/api/admin/partners", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ name, kind, is_active: true }),
    });
    setMsg(res.ok ? "Institution added." : "Failed — admin role required.");
    if (res.ok) { setName(""); load(); }
  }

  async function setRequest(id: number, status: string) {
    await fetch(`/api/admin/partnership-requests/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ status }),
    });
    load();
  }

  if (!token) return <Card className="p-6 text-center text-ink-2">Sign in with an admin account.</Card>;

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Step 20"
        title="Partnerships"
        subtitle="Manage partner institutions and review submitted partnership interests."
      />
      {msg && <p className="text-sm text-accent">{msg}</p>}

      <Card className="p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Add institution</h3>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex-1">
            <span className="text-xs text-ink-3">Name</span>
            <input value={name} onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
          </label>
          <label className="w-44">
            <span className="text-xs text-ink-3">Kind</span>
            <select value={kind} onChange={(e) => setKind(e.target.value)}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none">
              <option value="medical_college">Medical college</option>
              <option value="university">University</option>
              <option value="research_institute">Research institute</option>
              <option value="student_group">Student group</option>
              <option value="faculty">Faculty</option>
            </select>
          </label>
          <Button size="sm" onClick={createPartner}>Add</Button>
        </div>

        <h3 className="mt-6 mb-2 text-sm font-semibold uppercase tracking-wider text-ink-3">Institutions</h3>
        <div className="space-y-2">
          {partners.length === 0 && <p className="text-sm text-ink-3">No institutions yet.</p>}
          {partners.map((p) => (
            <div key={p.id} className="flex items-center justify-between rounded-lg bg-surface-2/40 px-3 py-2 text-sm">
              <div className="flex items-center gap-2 min-w-0">
                <span className="truncate font-medium">{p.name}</span>
                <Badge color="neutral">{p.kind}</Badge>
                {p.is_featured && <Badge color="accent">featured</Badge>}
              </div>
              <div className="flex gap-1">
                <Button size="sm" variant="secondary" onClick={async () => {
                  await fetch(`/api/admin/partners/${p.id}`, {
                    method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                    body: JSON.stringify({ is_featured: !p.is_featured }),
                  }); load();
                }}>{p.is_featured ? "Unfeature" : "Feature"}</Button>
                <Button size="sm" variant="secondary" onClick={async () => {
                  await fetch(`/api/admin/partners/${p.id}`, {
                    method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                    body: JSON.stringify({ is_active: !p.is_active }),
                  }); load();
                }}>{p.is_active ? "Deactivate" : "Activate"}</Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Partnership requests</h3>
        {requests.length === 0 ? (
          <p className="text-sm text-ink-3">No submitted requests.</p>
        ) : (
          <div className="space-y-3">
            {requests.map((r) => (
              <div key={r.id} className="rounded-xl bg-surface-2/40 p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{r.organization_name}</p>
                    <p className="text-xs text-ink-3">{r.contact_name} · {r.contact_email} · {r.organization_type}</p>
                    {r.goal && <p className="mt-1 text-sm text-ink-2">{r.goal}</p>}
                  </div>
                  <Badge color={r.status === "accepted" ? "success" : "warning"}>{r.status}</Badge>
                </div>
                <div className="mt-3 flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => setRequest(r.id, "reviewing")}>Reviewing</Button>
                  <Button size="sm" variant="secondary" onClick={() => setRequest(r.id, "accepted")}>Accept</Button>
                  <Button size="sm" variant="danger" onClick={() => setRequest(r.id, "declined")}>Decline</Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
