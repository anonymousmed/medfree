import { Badge, Card, SectionHeading } from "@medfree/ui";
import { fetchBooks } from "@/lib/api";
import { LibraryClient } from "@/components/LibraryClient";

export default async function LibraryPage() {
  const books = await fetchBooks();

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionHeading
        eyebrow="Knowledge foundation"
        title="Books & Research"
        subtitle="The reference layer underpinning every topic. Rights-aware, with admin-only uploads."
      />
      {/* Client-driven search + filters */}
      <LibraryClient serverBooks={books} />
    </div>
  );
}
