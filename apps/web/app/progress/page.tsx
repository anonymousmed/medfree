import { Card, ProgressBar, SectionHeading } from "@medfree/ui";

export default function ProgressPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionHeading
        eyebrow="Progress"
        title="Mastery & Analytics"
        subtitle="Personalized recommendations based on your study data."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Streak", "7 days"],
          ["Mastery", "61%"],
          ["MCQs", "312"],
          ["Viva", "48"],
        ].map(([t, v]) => (
          <Card key={t}>
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">{t}</p>
            <p className="mt-1 text-3xl font-bold">{v}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <p className="mb-3 font-semibold">Subject mastery</p>
          <div className="space-y-3">
            <ProgressBar value={72} label="Anatomy" />
            <ProgressBar value={55} label="Physiology" />
            <ProgressBar value={41} label="Biochemistry" />
          </div>
        </Card>
        <Card>
          <p className="mb-3 font-semibold">Weak areas</p>
          <div className="space-y-2 text-sm text-ink-2">
            <p className="rounded-lg bg-surface-2/50 px-3 py-2">Thorax — 41% <span className="text-accent">→ Revise</span></p>
            <p className="rounded-lg bg-surface-2/50 px-3 py-2">Brachial plexus lesions — Low <span className="text-accent">→ Review</span></p>
          </div>
        </Card>
      </div>
    </div>
  );
}
