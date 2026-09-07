"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";

type Res = {
  id: number; title: string; resource_type: string; rights_status: string;
  review_status: string; visibility: string; ai_usage_status: string;
};
type Review = Res;
type Report = {
  id: number; target_type: string; target_id?: number | null; target_slug?: string | null;
  category: string; title?: string | null; detail?: string | null; status: string; created_at?: string | null;
};
type Ad = {
  id: number; placement: string; title?: string | null; target_url?: string | null;
  is_active: boolean; priority: number; campaign_id?: string | null;
};

export function AdminContent() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [tab, setTab] = useState<"resources" | "reports">("resources");
  const [resources, setResources] = useState<Res[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [ads, setAds] = useState<Ad[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    const h = { Authorization: `Bearer ${token}` };
    const [r, rep, ad] = await Promise.all([
      fetch("/api/admin/reviews", { headers: h }).then((x) => x.json()).catch(() => []),
      fetch("/api/admin/reports", { headers: h }).then((x) => x.json()).catch(() => []),
      fetch("/api/admin/ads", { headers: h }).then((x) => x.json()).catch(() => []),
    ]);
    setResources(r);
    setReports(rep);
    setAds(ad);
  }, [token]);

  useEffect(() => { if (token) load(); }, [load, token]);

  async function review(id: number, decision: string) {
    const res = await fetch(`/api/admin/resources/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ decision }),
    });
    setMsg(res.ok ? `Resource ${id} → ${decision}` : "Action failed (rights gate may block publish).");
    load();
  }

  async function archive(id: number) {
    const res = await fetch(`/api/admin/resources/${id}`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` },
    });
    setMsg(res.ok ? `Resource ${id} archived.` : "Failed.");
    load();
  }

  async function resolveReport(id: number, status: string) {
    await fetch(`/api/admin/reports/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ status }),
    });
    load();
  }

  if (!token) return <Card className="p-6 text-center text-ink-2">Sign in with an admin account.</Card>;

  return (
    <div className="space-y-6">
      <SectionHeading eyebrow="Admin content" title="Content, reviews & reports" subtitle="Manage resources, the review workflow and the error-report queue." />
      {msg && <p className="text-sm text-accent">{msg}</p>}

      <div className="flex flex-wrap gap-2">
        <button onClick={() => setTab("resources")}
          className={`rounded-full px-4 py-2 text-sm ${tab === "resources" ? "bg-accent text-white" : "border border-surface-2"}`}>Resources & reviews</button>
        <button onClick={() => setTab("reports")}
          className={`rounded-full px-4 py-2 text-sm ${tab === "reports" ? "bg-accent text-white" : "border border-surface-2"}`}>Reports ({reports.length})</button>
      </div>

      {tab === "resources" && (
        <>
          <Card className="p-5">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Review queue</h3>
            {resources.length === 0 ? (
              <p className="text-sm text-ink-3">No resources awaiting review.</p>
            ) : (
              <div className="space-y-3">
                {resources.map((r) => (
                  <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-2/40 p-3">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{r.title}</p>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        <Badge color="neutral">{r.resource_type}</Badge>
                        <Badge color={r.rights_status === "review_required" ? "warning" : "success"}>{r.rights_status}</Badge>
                        <Badge color="neutral">{r.review_status}</Badge>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => review(r.id, "approve")}>Approve</Button>
                      <Button size="sm" variant="danger" onClick={() => review(r.id, "reject")}>Reject</Button>
                      <Button size="sm" variant="secondary" onClick={() => review(r.id, "publish")}>Publish</Button>
                      <Button size="sm" variant="secondary" onClick={() => archive(r.id)}>Archive</Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-5">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Ad placements</h3>
            {ads.length === 0 ? <p className="text-sm text-ink-3">No ads yet.</p> : (
              <div className="space-y-2">
                {ads.map((a) => (
                  <div key={a.id} className="flex items-center justify-between rounded-lg bg-surface-2/40 px-3 py-2 text-sm">
                    <div className="min-w-0">
                      <span className="font-medium">{a.title ?? "Untitled"}</span>
                      <span className="ml-2 text-ink-3">{a.placement} · p{a.priority}</span>
                    </div>
                    <Badge color={a.is_active ? "success" : "neutral"}>{a.is_active ? "active" : "inactive"}</Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}

      {tab === "reports" && (
        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Error reports</h3>
          {reports.length === 0 ? <p className="text-sm text-ink-3">No reports submitted.</p> : (
            <div className="space-y-3">
              {reports.map((rep) => (
                <div key={rep.id} className="rounded-xl bg-surface-2/40 p-3">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0">
                      <p className="font-medium">{rep.category}</p>
                      <p className="text-xs text-ink-3">{rep.target_type} · {rep.target_slug ?? "#" + (rep.target_id ?? "")}</p>
                      {rep.title && <p className="mt-1 text-sm text-ink-1">{rep.title}</p>}
                      {rep.detail && <p className="text-sm text-ink-2">{rep.detail}</p>}
                    </div>
                    <Badge color={rep.status === "resolved" ? "success" : "warning"}>{rep.status}</Badge>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <Button size="sm" variant="secondary" onClick={() => resolveReport(rep.id, "under_review")}>Reviewing</Button>
                    <Button size="sm" variant="secondary" onClick={() => resolveReport(rep.id, "resolved")}>Resolve</Button>
                    <Button size="sm" variant="danger" onClick={() => resolveReport(rep.id, "dismissed")}>Dismiss</Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
