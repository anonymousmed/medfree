"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Button, Card } from "@medfree/ui";
import { useAuth } from "./AuthProvider";
import { AdminInsights } from "./AdminInsights";
import { AdminPartners } from "./AdminPartners";
import { AdminUpload } from "./AdminUpload";
import { AdminContent } from "./AdminContent";
import { AdminCreate } from "./AdminCreate";

type User = { id: number; email?: string; is_active: boolean; roles: string[] };
type Res = { id: number; title: string; resource_type: string; rights_status: string; review_status: string; visibility: string; ai_usage_status?: string; read_url?: string | null };
type TabKey = "content" | "upload" | "create" | "manage" | "insights" | "partners";

export function AdminPortal() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [tab, setTab] = useState<TabKey>("content");
  const [stats, setStats] = useState<{ users: number; resources: number; pending_reviews: number } | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [resources, setResources] = useState<Res[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [annTitle, setAnnTitle] = useState("");
  const [adTitle, setAdTitle] = useState("");
  const [adUrl, setAdUrl] = useState("/atlas");
  const [platformMsg, setPlatformMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    const h = { Authorization: `Bearer ${token}` };
    const [s, u, r] = await Promise.all([
      fetch("/api/admin/stats", { headers: h }).then((x) => x.json()),
      fetch("/api/admin/users", { headers: h }).then((x) => x.json()),
      fetch("/api/admin/resources", { headers: h }).then((x) => x.json()),
    ]);
    setStats(s);
    setUsers(u);
    setResources(r);
  }, [token]);

  useEffect(() => { if (token) load(); }, [load, token]);

  async function publishAnnouncement() {
    if (!annTitle.trim()) return;
    const res = await fetch("/api/admin/announcements", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ kind: "system", title: annTitle, is_active: true }),
    });
    setPlatformMsg(res.ok ? "Announcement published." : "Failed — admin role required.");
    if (res.ok) setAnnTitle("");
  }

  async function publishAd() {
    const res = await fetch("/api/admin/ads", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ placement: "homepage", title: adTitle, target_url: adUrl, is_active: true, priority: 1 }),
    });
    setPlatformMsg(res.ok ? "Ad created for the homepage placement." : "Failed — admin role required.");
    if (res.ok) setAdTitle("");
  }

  async function decide(id: number, decision: string) {
    const res = await fetch(`/api/admin/resources/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ decision }),
    });
    if (res.ok) { setMessage(`Resource ${id} → ${decision}`); load(); }
    else { const b = await res.json(); setMessage(b.detail ?? "Action failed"); }
  }

  if (!token) return <Card>Sign in with an admin account to access the admin panel.</Card>;

  if (tab === "upload") {
    return (
      <div className="space-y-6">
        <TabBar tab={tab} setTab={setTab} />
        <AdminUpload />
      </div>
    );
  }
  if (tab === "create") {
    return (
      <div className="space-y-6">
        <TabBar tab={tab} setTab={setTab} />
        <AdminCreate />
      </div>
    );
  }
  if (tab === "manage") {
    return (
      <div className="space-y-6">
        <TabBar tab={tab} setTab={setTab} />
        <AdminContent />
      </div>
    );
  }
  if (tab === "insights") {
    return (
      <div className="space-y-6">
        <TabBar tab={tab} setTab={setTab} />
        <AdminInsights />
      </div>
    );
  }
  if (tab === "partners") {
    return (
      <div className="space-y-6">
        <TabBar tab={tab} setTab={setTab} />
        <AdminPartners />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <TabBar tab={tab} setTab={setTab} />
      {message && <p className="text-sm text-accent">{message}</p>}

      {stats && (
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            ["Users", stats.users],
            ["Resources", stats.resources],
            ["Pending reviews", stats.pending_reviews],
          ].map(([k, v]) => (
            <Card key={k}>
              <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">{k}</p>
              <p className="mt-1 text-3xl font-bold">{v}</p>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <p className="mb-3 font-semibold">Resource review workflow (admin-only)</p>
        <div className="max-h-96 overflow-auto rounded-xl bg-surface-2/40 p-1">
          {resources.length === 0 && <p className="p-3 text-sm text-ink-3">No resources.</p>}
          {resources.map((r) => (
            <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg px-3 py-2.5">
              <div className="min-w-0">
                <p className="truncate font-medium">{r.title}</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  <Badge color="neutral">{r.resource_type}</Badge>
                  <Badge color={r.rights_status === "review_required" ? "warning" : "success"}>{r.rights_status}</Badge>
                  <Badge color={r.review_status === "published" ? "success" : "neutral"}>{r.review_status}</Badge>
                </div>
              </div>
              <div className="flex gap-2">
                {r.read_url && (
                  <Link href={`/read/${r.id}`}
                    className="rounded-xl border border-surface-2 px-3 py-1.5 text-xs font-medium text-ink-2 hover:border-accent/40 hover:text-accent">
                    Read online
                  </Link>
                )}
                <Button size="sm" onClick={() => decide(r.id, "approve")}>Approve</Button>
                <Button size="sm" onClick={() => decide(r.id, "reject")} variant="danger">Reject</Button>
                <Button size="sm" onClick={() => decide(r.id, "publish")} variant="secondary">Publish</Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <p className="mb-3 font-semibold">Users</p>
        <div className="max-h-72 overflow-auto rounded-xl bg-surface-2/40 p-1">
          {users.length === 0 && <p className="p-3 text-sm text-ink-3">No users.</p>}
          {users.map((u) => (
            <div key={u.id} className="flex items-center justify-between rounded-lg px-3 py-2">
              <span className="truncate text-sm">{u.email}</span>
              <div className="flex gap-1">{u.roles.map((r) => <Badge key={r} color="accent">{r}</Badge>)}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <p className="mb-3 font-semibold">Announcements & Advertisement placement (Step 15)</p>
        <div className="space-y-4">
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex-1">
              <span className="text-xs text-ink-3">Announcement title</span>
              <input value={annTitle} onChange={(e) => setAnnTitle(e.target.value)}
                className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
            </label>
            <Button size="sm" onClick={publishAnnouncement}>Publish announcement</Button>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex-1">
              <span className="text-xs text-ink-3">Ad title</span>
              <input value={adTitle} onChange={(e) => setAdTitle(e.target.value)}
                className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
            </label>
            <label className="w-40">
              <span className="text-xs text-ink-3">Target URL</span>
              <input value={adUrl} onChange={(e) => setAdUrl(e.target.value)} placeholder="/atlas"
                className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
            </label>
            <Button size="sm" onClick={publishAd}>Create ad</Button>
          </div>
          {platformMsg && <p className="text-sm text-accent">{platformMsg}</p>}
        </div>
      </Card>
    </div>
  );
}

function TabBar({ tab, setTab }: { tab: TabKey; setTab: (t: TabKey) => void }) {
  const tabs: { key: TabKey; label: string }[] = [
    { key: "content", label: "Content & users" },
    { key: "upload", label: "Upload" },
    { key: "create", label: "Create" },
    { key: "manage", label: "Reviews & reports" },
    { key: "insights", label: "Analytics & audit" },
    { key: "partners", label: "Partnerships" },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((t) => (
        <button key={t.key} onClick={() => setTab(t.key)}
          className={`rounded-full px-4 py-2 text-sm font-medium ${
            tab === t.key ? "bg-accent text-white" : "border border-surface-2 text-ink-2 hover:border-accent/40"
          }`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}
