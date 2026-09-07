"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import type { AiAnswer } from "@/lib/studyApi";

interface Policy {
  unknown_is_excluded: boolean;
  review_required_is_excluded: boolean;
  only_ai_allowed_ingested: boolean;
}

const SUGGESTIONS = [
  "What forms the brachial plexus?",
  "Describe the blood supply of the upper limb.",
  "What happens with a fracture of the tibia?",
];

export function AssistantClient() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AiAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/ai/ingestion-policy").then((r) => r.json()).then(setPolicy).catch(() => setPolicy(null));
  }, []);

  const ask = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await fetch("/api/ai/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? "Request failed");
      setAnswer(await res.json());
    } catch (e: any) {
      setError(e?.message ?? "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeading
        eyebrow="Step 13"
        title="AI Study Assistant"
        subtitle="Ask a question and get an answer grounded in approved MEDFREE content, with citations."
      />

      {policy && (
        <Card className="p-4">
          <div className="flex flex-wrap gap-3 text-xs">
            <Badge color="accent">Answers grounded in approved content only</Badge>
            <Badge>{policy.unknown_is_excluded ? "unknown → excluded" : "unknown allowed"}</Badge>
            <Badge>{policy.review_required_is_excluded ? "review_required → excluded" : ""}</Badge>
          </div>
        </Card>
      )}

      <Card className="p-6">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") ask(question); }}
            placeholder="Ask a first-year MBBS question…"
            className="flex-1 rounded-xl border border-surface-2 bg-surface-1 px-4 py-3 text-sm text-ink-1 placeholder:text-ink-3 focus:border-accent focus:outline-none"
          />
          <Button onClick={() => ask(question)} disabled={loading}>
            {loading ? "Thinking…" : "Ask"}
          </Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => { setQuestion(s); ask(s); }}
              className="rounded-full border border-surface-2 px-3 py-1 text-xs text-ink-2 hover:border-accent/40">
              {s}
            </button>
          ))}
        </div>
      </Card>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {answer && (
        <Card className="p-6">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-1">{answer.answer}</p>
          <p className="mt-4 text-xs text-ink-3">{answer.disclaimer}</p>

          {answer.sources.length > 0 && (
            <div className="mt-5 border-t border-surface-2 pt-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-ink-3">Sources cited</h3>
              <ul className="mt-2 space-y-1">
                {answer.sources.map((s, i) => (
                  <li key={i} className="text-sm text-ink-2">
                    <span className="text-ink-3">[{s.source_type}]</span> {s.title}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
