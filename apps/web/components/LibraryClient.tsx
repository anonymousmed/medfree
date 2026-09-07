"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Badge, Card } from "@medfree/ui";
import type { Book } from "@/lib/api";

const SUBJECTS = ["anatomy", "physiology", "biochemistry"];

export function LibraryClient({ serverBooks }: { serverBooks: Book[] }) {
  const [books, setBooks] = useState<Book[]>(serverBooks);
  const [q, setQ] = useState("");
  const [subject, setSubject] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (query: string, subj: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (subj) params.set("subject", subj);
      if (query) params.set("q", query);
      const res = await fetch(`/api/books?${params.toString()}`);
      if (res.ok) setBooks(await res.json());
    } catch {
      /* keep current */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(q, subject), 400);
    return () => clearTimeout(t);
  }, [q, subject, load]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search by title…"
          className="h-11 flex-1 rounded-xl border border-surface-2 bg-surface-2/50 px-3 text-sm focus:border-accent focus:outline-none"
        />
        <div className="flex gap-2">
          <button
            onClick={() => setSubject("")}
            className={`rounded-full px-3 py-1.5 text-xs font-medium ${subject === "" ? "bg-accent text-white" : "bg-surface-2 text-ink-2"}`}
          >All</button>
          {SUBJECTS.map((s) => (
            <button key={s} onClick={() => setSubject(s)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium ${subject === s ? "bg-accent text-white" : "bg-surface-2 text-ink-2"}`}
            >{s}</button>
          ))}
        </div>
      </div>

      {loading && <p className="text-sm text-ink-3">Searching…</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {books.length === 0 && !loading && (
          <p className="text-sm text-ink-3 col-span-full">No books match your filters.</p>
        )}
        {books.map((b) => (
          <Card key={b.id} className="h-full transition hover:border-accent/40">
            <div className="flex items-start justify-between">
              <Badge color="neutral">{b.subject_slug ?? "resource"}</Badge>
              {b.license_name && <Badge color="accent">{b.license_name}</Badge>}
            </div>
            <h3 className="mt-3 font-semibold">{b.title}</h3>
            {b.author && <p className="mt-1 text-sm text-ink-3">by {b.author.name}</p>}
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink-3">
              {b.edition && <span>{b.edition}</span>}
              {b.year && <span>· {b.year}</span>}
              {b.rights_status && <Badge color={b.rights_status === "open_license" ? "success" : "warning"}>{b.rights_status}</Badge>}
            </div>
            <Link href={`/library/${b.id}`} className="mt-3 block text-sm text-accent hover:underline">
              Read in library →
            </Link>
          </Card>
        ))}
      </div>
    </div>
  );
}
