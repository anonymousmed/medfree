"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge, Button, Card } from "@medfree/ui";
import { useAuth } from "./AuthProvider";
import { fetchResource, type Resource } from "@/lib/api";

/**
 * In-browser PDF reader.
 *
 * Renders the PDF inline on MEDFREE so users read it on the site — no external
 * drive, no forced download. The file is served from Supabase Storage with
 * `Content-Type: application/pdf` (no `Content-Disposition: attachment`), so the
 * browser's built-in viewer renders it inline.
 *
 * The reader gives a clean embedded surface with fullscreen support. If the
 * resource has no public, in-browser URL (e.g. it's a private draft), we show a
 * clear message instead of a broken frame.
 */
export function PdfReader({ resourceId }: { resourceId: number }) {
  const router = useRouter();
  const { session } = useAuth();
  const token = session?.access_token;
  const [resource, setResource] = useState<Resource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    fetchResource(resourceId)
      .then((r) => {
        if (!alive) return;
        const readable = ["book", "pdf", "document", "slides", "article", "notes"].includes(r.resource_type);
        if (!readable) setError("This item is not a readable document.");
        else if (!r.read_url) setError("This document is not available for online reading yet.");
        setResource(r);
      })
      .catch(() => alive && setError("Could not load this document."))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [resourceId]);

  // Record real reading time on MEDFREE (not external storage).
  useEffect(() => {
    if (!token) return;
    const send = () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
      fetch("/api/progress/track", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ kind: "reading", seconds: 30, resource_id: resourceId, path: `/read/${resourceId}` }),
      }).catch(() => {});
    };
    const first = setTimeout(send, 5000);
    const id = setInterval(send, 30000);
    return () => {
      clearTimeout(first);
      clearInterval(id);
    };
  }, [token, resourceId]);

  if (loading) {
    return (
      <Card className="flex min-h-[420px] items-center justify-center p-6 text-sm text-ink-3">
        Loading reader…
      </Card>
    );
  }

  if (error || !resource) {
    return (
      <Card className="space-y-4 p-8 text-center">
        <p className="text-sm text-ink-2">{error ?? "Document unavailable."}</p>
        <Button variant="secondary" onClick={() => router.back()}>Go back</Button>
      </Card>
    );
  }

  const viewerUrl = resource.read_url!;

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surface-2 px-5 py-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="truncate text-lg font-semibold">{resource.title}</h1>
            <Badge color="neutral">{resource.resource_type}</Badge>
          </div>
          {(resource.creator || resource.publisher) && (
            <p className="mt-0.5 text-xs text-ink-3">
              {resource.creator ? `by ${resource.creator}` : ""}
              {resource.creator && resource.publisher ? " · " : ""}
              {resource.publisher ?? ""}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => router.back()}>Back</Button>
          <a href={viewerUrl} target="_blank" rel="noreferrer"
             className="rounded-xl border border-surface-2 px-4 py-2 text-sm font-medium text-ink-2 hover:border-accent/40 hover:text-accent">
            Open full screen ↗
          </a>
        </div>
      </div>

      <div className="bg-surface-2/40">
        <iframe
          src={viewerUrl}
          title={resource.title}
          className="h-[78vh] w-full"
          style={{ border: 0 }}
        />
      </div>

      <p className="px-5 py-3 text-xs text-ink-3">
        Reading on MEDFREE · hosted on our own storage · no external link needed.
      </p>
    </Card>
  );
}
