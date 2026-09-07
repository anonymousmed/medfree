import Link from "next/link";
import { Card, SectionHeading } from "@medfree/ui";
import { fetchSubjects, fetchTopics } from "@/lib/api";

export default async function LearnPage() {
  const subjects = await fetchSubjects();
  const topics = await fetchTopics("anatomy");

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <SectionHeading
        eyebrow="Learn"
        title="Subjects & Topics"
        subtitle="Every topic follows the same flow: overview → atlas → clinical → practice → books → mastery."
      />

      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Subjects</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subjects.map((s) => (
            <Link key={s.slug} href={`/learn/${s.slug}`}>
              <Card className="h-full transition hover:border-accent/40">
                <span className="grid h-10 w-10 place-items-center rounded-lg text-white" style={{ background: s.color }}>
                  {s.title[0]}
                </span>
                <div className="mt-3 flex items-center justify-between">
                  <h4 className="font-semibold">{s.title}</h4>
                  <span className="text-accent">→</span>
                </div>
                <p className="mt-1 text-sm text-ink-3">{s.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-3">Anatomy topics</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {topics.map((t) => (
            <Link key={t.id} href={`/learn/anatomy/${t.slug}`}>
              <Card className="h-full transition hover:border-accent/40">
                <h4 className="font-semibold">{t.title}</h4>
                <p className="mt-1 text-sm text-ink-3">{t.summary}</p>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
