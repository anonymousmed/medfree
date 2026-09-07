"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";

type Analytics = {
  period_days: number;
  users: { total: number; active: number; new_last_30d: number };
  learning: { topics_completed: number; quiz_attempts: number; quiz_correct: number; quiz_accuracy: number };
  search: { volume: number; failed: number; top_queries: { query: string; count: number }[] };
  atlas: { top_structures: { structure: string; count: number }[] };
  topics: { most_engaged: { title: string; count: number }[] };
};

type AuditRow = {
  id: number;
  actor_email?: string | null;
  action: string;
  target_type?: string | null;
  target_id?: number | null;
  detail?: string | null;
  ip_address?: string | null;
  success: boolean;
  created_at?: string | null;
};

export function AdminInsights() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const h = { Authorization: `Bearer ${token}` } as Record<string, string>;
    try {
      const [a, l] = await Promise.all([
        fetch("/api/admin/analytics", { headers: h }).then((r) => (r.ok ? r.json() : null)),
        fetch("/api/admin/audit-logs", { headers: h }).then((r) => (r.ok ? r.json() : [])),
      ]);
      if (!a) throw new Error("Admin role required for analytics.");
      setAnalytics(a);
      setAudit(l);
    } catch (e: any) {
      setError(e?.message ?? "Could not load insights.");
    }
  }, [token]);

  useEffect(() => { if (token) load(); }, [load, token]);

  if (!token) {
    return <Card className="p-6 text-center text-ink-2">Sign in with an admin account to view analytics & audit logs.</Card>;
  }

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Steps 16 & 17"
        title="Analytics & Security Audit"
        subtitle="Product/learning/search analytics plus the privileged-mutation audit trail."
      />
      {error && <p className="text-sm text-red-500">{error}</p>}

      {analytics && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Total users" value={analytics.users.total} />
            <Stat label="Active users" value={analytics.users.active} />
            <Stat label="New (30d)" value={analytics.users.new_last_30d} />
            <Stat label="Topics completed" value={analytics.learning.topics_completed} />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Learning</h3>
              <div className="grid grid-cols-2 gap-3">
                <Mini label="Quiz attempts" value={analytics.learning.quiz_attempts} />
                <Mini label="Quiz accuracy" value={`${analytics.learning.quiz_accuracy}%`} />
              </div>
            </Card>
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Search</h3>
              <div className="grid grid-cols-2 gap-3">
                <Mini label="Volume" value={analytics.search.volume} />
                <Mini label="Failed" value={analytics.search.failed} />
              </div>
              {analytics.search.top_queries.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {analytics.search.top_queries.slice(0, 5).map((q) => (
                    <li key={q.query} className="flex justify-between text-sm">
                      <span className="truncate text-ink-2">{q.query}</span>
                      <span className="text-ink-3">{q.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </>
      )}

      <Card className="p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Audit log (recent privileged actions)</h3>
        {audit.length === 0 ? (
          <p className="text-sm text-ink-3">No admin actions recorded yet.</p>
        ) : (
          <div className="max-h-96 overflow-auto rounded-xl bg-surface-2/40 p-1">
            {audit.map((r) => (
              <div key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm">
                <div className="min-w-0">
                  <span className="font-medium">{r.action}</span>
                  <span className="ml-2 text-ink-3">{r.actor_email}</span>
                  {r.target_id && <span className="ml-2 text-ink-3">#{r.target_id}</span>}
                </div>
                <div className="flex items-center gap-2">
                  <Badge color={r.success ? "success" : "danger"}>{r.success ? "ok" : "failed"}</Badge>
                  {r.created_at && <span className="text-xs text-ink-3">{new Date(r.created_at).toLocaleString()}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-5">
      <p className="text-xs uppercase tracking-wider text-ink-3">{label}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
    </Card>
  );
}

function Mini({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-surface-2 bg-surface-1 p-3 text-center">
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs text-ink-3">{label}</p>
    </div>
  );
}
