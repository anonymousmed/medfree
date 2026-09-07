import Link from "next/link";
import { Badge, Card, ProgressBar, SectionHeading } from "@medfree/ui";
import { fetchSubjects, fetchTopics } from "@/lib/api";
import { NAV_ITEMS } from "@medfree/config";
import { HomepageBanner } from "@/components/HomepageBanner";

export default async function HomePage() {
  const subjects = await fetchSubjects();
  const topics = await fetchTopics();
  const continueTopic = topics[0];

  return (
    <div className="mx-auto max-w-6xl space-y-10">
      {/* Admin announcements + controlled placement banner */}
      <HomepageBanner />

      {/* Hero — Human Atlas is the headline, not "Browse Books" */}
      <section className="relative overflow-hidden rounded-3xl border border-surface-2 bg-surface-1 p-8 md:p-12">
        <div className="max-w-2xl">
          <Badge color="accent">Free digital medical university</Badge>
          <h1 className="mt-4 text-3xl font-bold leading-tight md:text-5xl">
            Learn medicine through{" "}
            <span className="text-accent">the Human Atlas</span>.
          </h1>
          <p className="mt-3 text-ink-2 md:text-lg">
            Interactive 3D anatomy, visual explanations, clinical cases, MCQs,
            viva and flashcards — with books and research as your reference layer.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/atlas"
              className="rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white hover:brightness-110"
            >
              Explore the Atlas →
            </Link>
            <Link
              href="/learn"
              className="rounded-xl border border-surface-2 bg-surface-2 px-5 py-3 text-sm font-semibold text-ink-1 hover:bg-surface-3"
            >
              Start Learning
            </Link>
          </div>
          <p className="mt-4 text-xs uppercase tracking-wider text-ink-3">
            Learn → Explore → Practice → Master
          </p>
        </div>
      </section>

      {/* Continue learning */}
      {continueTopic && (
        <section>
          <SectionHeading
            eyebrow="Continue learning"
            title="Pick up where you left off"
            action={<Link href={`/learn/${continueTopic.slug}`} className="text-sm text-accent">Open</Link>}
          />
          <Card className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-ink-3">ANATOMY</p>
              <h3 className="mt-1 text-lg font-semibold">{continueTopic.title}</h3>
              <p className="mt-1 text-sm text-ink-2">{continueTopic.summary}</p>
            </div>
            <div className="flex flex-col justify-end gap-2">
              <ProgressBar value={continueTopic.mastery ?? 0} label="Mastery" />
              <Link href={`/learn/${continueTopic.slug}`} className="text-sm text-accent hover:underline">
                Continue →
              </Link>
            </div>
          </Card>
        </section>
      )}

      {/* Human Atlas — centerpiece */}
      <section>
        <SectionHeading
          eyebrow="Centerpiece"
          title="Human Atlas"
          subtitle="Rotate, zoom, isolate, search and identify structures across systems & regions."
          action={<Link href="/atlas" className="text-sm text-accent hover:underline">Open Atlas</Link>}
        />
        <Link href="/atlas">
          <Card className="group overflow-hidden p-0">
            <div className="grid place-items-center bg-gradient-to-br from-surface-2 to-surface-1 py-16">
              <span className="text-5xl">🧠</span>
            </div>
            <div className="flex items-center justify-between px-5 py-4">
              <div>
                <p className="font-semibold">Interactive 3D & structure identification</p>
                <p className="text-sm text-ink-3">Systems · Regions · Clinical · Quiz · Viva</p>
              </div>
              <span className="text-accent group-hover:translate-x-1 transition">→</span>
            </div>
          </Card>
        </Link>
      </section>

      {/* Detailed Atlas — deep-dive 3D (external, CC BY 4.0) */}
      <section>
        <SectionHeading
          eyebrow="Detailed Human Atlas"
          title="High-resolution 3D explorer"
          subtitle="2,234 selectable meshes, system layers, search and exploded views — an open-source, CC BY 4.0 deep dive."
          action={
            <Link href="/detailed-atlas" className="text-sm text-accent hover:underline">
              Open Detailed Atlas
            </Link>
          }
        />
        <Link href="/detailed-atlas">
          <Card className="group overflow-hidden p-0">
            <div className="grid place-items-center bg-gradient-to-br from-surface-2 to-surface-1 py-16">
              <span className="text-5xl">🩻</span>
            </div>
            <div className="flex items-center justify-between px-5 py-4">
              <div>
                <p className="font-semibold">Detailed Human Atlas</p>
                <p className="text-sm text-ink-3">2,234 meshes · Search · Layers · Exploded views</p>
              </div>
              <span className="text-accent group-hover:translate-x-1 transition">→</span>
            </div>
          </Card>
        </Link>
      </section>

      {/* Subjects */}
      <section>
        <SectionHeading
          eyebrow="Subjects"
          title="First-year curriculum"
          action={<Link href="/learn" className="text-sm text-accent hover:underline">All subjects</Link>}
        />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subjects.map((s) => (
            <Link key={s.slug} href={`/learn/${s.slug}`}>
              <Card className="h-full transition hover:-translate-y-0.5 hover:border-accent/40">
                <span className="grid h-10 w-10 place-items-center rounded-lg text-white" style={{ background: s.color }}>
                  {s.title[0]}
                </span>
                <h3 className="mt-3 font-semibold">{s.title}</h3>
                <p className="mt-1 text-sm text-ink-3">{s.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Practice */}
      <section>
        <SectionHeading eyebrow="Practice" title="Test & reinforce" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["MCQs", "Timed, clinical & anatomy identification", "/practice"],
            ["Viva", "Question → answer → model answer", "/practice"],
            ["Flashcards", "Spaced repetition", "/flashcards"],
            ["Practicals", "Step-by-step & spotter mode", "/practicals"],
          ].map(([t, d, h]) => (
            <Link key={t} href={h}>
              <Card className="h-full transition hover:border-accent/40">
                <p className="font-semibold">{t}</p>
                <p className="mt-1 text-sm text-ink-3">{d}</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Books — reference layer */}
      <section>
        <SectionHeading
          eyebrow="Knowledge foundation"
          title="Books & Research"
          subtitle="The reference layer that supports every topic."
          action={<Link href="/library" className="text-sm text-accent hover:underline">Library</Link>}
        />
      </section>
    </div>
  );
}
