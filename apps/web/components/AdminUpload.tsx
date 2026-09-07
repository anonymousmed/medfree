"use client";

import { useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";

type Presign = { storage_key: string; upload_url: string; expires_in: number };

const RESOURCE_TYPES = ["book", "pdf", "epub", "image", "diagram", "3d", "video", "audio", "slides", "dataset", "notes", "article"];

export function AdminUpload() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [file, setFile] = useState<File | null>(null);
  const [meta, setMeta] = useState({
    resource_type: "book", title: "", creator: "", publisher: "", source_url: "",
    license_name: "", rights_status: "open_license", ai_usage_status: "true",
    attribution_text: "", visibility: "public",
  });
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function upload() {
    if (!file || !meta.title.trim()) { setMsg("Choose a file and enter a title."); return; }
    setBusy(true);
    setMsg(null);
    try {
      const h = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
      // 1) presign
      const presignRes = await fetch("/api/storage/presign", {
        method: "POST", headers: h,
        body: JSON.stringify({ filename: file.name, resource_type: meta.resource_type }),
      });
      if (!presignRes.ok) throw new Error("presign failed (file type may not be allowed)");
      const presign: Presign = await presignRes.json();

      // 2) PUT bytes (local dev uses a local target; S3 uses presigned URL)
      if (!presign.upload_url.startsWith("local://")) {
        await fetch(presign.upload_url, { method: "PUT", body: file });
      }

      // 3) confirm metadata
      const confirmRes = await fetch("/api/storage/confirm", {
        method: "POST", headers: h,
        body: JSON.stringify({
          storage_key: presign.storage_key, filename: file.name,
          ...meta,
        }),
      });
      if (!confirmRes.ok) {
        const b = await confirmRes.json();
        throw new Error(b?.detail ?? "confirm failed (rights gate may block public publish)");
      }
      setMsg("Upload complete. Resource created.");
      setFile(null);
      setMeta((m) => ({ ...m, title: "" }));
    } catch (e: any) {
      setMsg(e?.message ?? "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!token) return <Card className="p-6 text-center text-ink-2">Sign in with an admin account to upload.</Card>;

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Admin upload"
        title="Upload a resource"
        subtitle="Only admins can upload books & platform resources — enforced at the backend."
      />

      <Card className="p-6 space-y-4">
        <div>
          <span className="text-xs font-medium text-ink-3">File</span>
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block w-full text-sm text-ink-2 file:mr-3 file:rounded-xl file:border-0 file:bg-surface-2 file:px-3 file:py-2 file:text-ink-1" />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-xs font-medium text-ink-3">Resource type</span>
            <select value={meta.resource_type} onChange={(e) => setMeta({ ...meta, resource_type: e.target.value, ...(e.target.value === "3d" ? { resource_type: "3d" } : {}) })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none">
              {RESOURCE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-3">Title</span>
            <input value={meta.title} onChange={(e) => setMeta({ ...meta, title: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-3">Creator</span>
            <input value={meta.creator} onChange={(e) => setMeta({ ...meta, creator: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-3">Publisher</span>
            <input value={meta.publisher} onChange={(e) => setMeta({ ...meta, publisher: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
          </label>
          <label className="block sm:col-span-2">
            <span className="text-xs font-medium text-ink-3">Source URL</span>
            <input value={meta.source_url} onChange={(e) => setMeta({ ...meta, source_url: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
          </label>

          <label className="block">
            <span className="text-xs font-medium text-ink-3">Rights status</span>
            <select value={meta.rights_status} onChange={(e) => setMeta({ ...meta, rights_status: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none">
              <option value="open_license">Open license</option>
              <option value="public_domain">Public domain</option>
              <option value="permission_granted">Permission granted</option>
              <option value="external_only">External only</option>
              <option value="review_required">Review required</option>
              <option value="blocked">Blocked</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-3">AI usage</span>
            <select value={meta.ai_usage_status} onChange={(e) => setMeta({ ...meta, ai_usage_status: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none">
              <option value="true">Allowed</option>
              <option value="false">Not allowed</option>
              <option value="unknown">Unknown</option>
            </select>
          </label>
          <label className="block sm:col-span-2">
            <span className="text-xs font-medium text-ink-3">Attribution</span>
            <input value={meta.attribution_text} onChange={(e) => setMeta({ ...meta, attribution_text: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none" />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-3">Visibility</span>
            <select value={meta.visibility} onChange={(e) => setMeta({ ...meta, visibility: e.target.value })}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none">
              <option value="public">Public</option>
              <option value="private">Private (draft)</option>
            </select>
          </label>
        </div>

        <div className="flex items-center gap-3">
          <Button onClick={upload} disabled={busy}>{busy ? "Uploading…" : "Upload"}</Button>
          {meta.rights_status === "review_required" && <Badge color="warning">review_required blocks public publish</Badge>}
          {meta.ai_usage_status === "unknown" && <Badge>unknown is NOT AI-ingested</Badge>}
        </div>
        {msg && <p className="text-sm text-accent">{msg}</p>}
      </Card>
    </div>
  );
}
