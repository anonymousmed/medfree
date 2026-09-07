import { Badge, Card, SectionHeading } from "@medfree/ui";
import { fetchBook } from "@/lib/api";
import { ReportError } from "@/components/ReportError";

export default async function BookReaderPage({ params }: { params: { id: string } }) {
  const book = await fetchBook(Number(params.id));
  const externalOnly = book.rights_status === "external_only";
  const isOpen = ["open_license", "public_domain", "permission_granted"].includes(book.rights_status ?? "");

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Badge color="accent">{book.subject_slug ?? "book"}</Badge>
          <h1 className="mt-2 text-3xl font-bold">{book.title}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink-3">
            {book.author && <span>by {book.author.name}</span>}
            {book.edition && <span>· {book.edition}</span>}
            {book.publisher && <span>· {book.publisher}</span>}
            {book.year && <span>· {book.year}</span>}
          </div>
        </div>
        <ReportError target_type="resource" target_id={book.id} target_slug={book.title} />
      </div>

      {/* Rights notice — keep honest about what we can host */}
      <Card className="border-accent/30 bg-accent-soft/10">
        <p className="text-sm text-ink-2">
          Rights: <Badge color={book.rights_status === "open_license" ? "success" : "warning"}>{book.rights_status ?? "unknown"}</Badge>
          {book.license_name && <span> ({book.license_name})</span>}
          {" — "}
          {isOpen ? "This resource is legally hosted per its license." :
            externalOnly ? "This resource is external-only: we link to the legitimate source and do not host a local copy." :
            "Availability is under review; content is not republished without a verified rights record."}
        </p>
      </Card>

      {/* Reading surface */}
      <Card>
        <SectionHeading eyebrow="Book reader" title="Chapters" />
        {book.chapters && book.chapters.length > 0 ? (
          <ul className="space-y-2">
            {book.chapters.map((c) => (
              <li key={c.id}>
                <div className="flex items-center justify-between rounded-lg bg-surface-2/50 px-3 py-2.5">
                  <div>
                    <p className="font-medium">{c.title}</p>
                    {c.topic_slug && <p className="text-xs text-accent">linked to topic: {c.topic_slug}</p>}
                  </div>
                  <span className="text-sm text-ink-3">Chapter {c.chapter_index + 1}</span>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-ink-3">No chapters linked yet.</p>
        )}

        <div className="mt-6 flex flex-wrap gap-3">
          {isOpen && (
            <a href={book.source_url ?? "#"} target="_blank" rel="noreferrer"
               className="rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white hover:brightness-110">
              Open/read source ↗
            </a>
          )}
          {externalOnly && (
            <a href={book.source_url} target="_blank" rel="noreferrer"
               className="rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white hover:brightness-110">
              Go to legitimate source ↗
            </a>
          )}
          {!isOpen && !externalOnly && (
            <span className="text-sm text-ink-3">Reader becomes available after rights review.</span>
          )}
        </div>
      </Card>
    </div>
  );
}
