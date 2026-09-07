import Link from "next/link";
import { Badge } from "@medfree/ui";
import type { TopicNode } from "@/lib/api";

function Group({
  label,
  nodes,
  subjectSlug,
  tone,
}: {
  label: string;
  nodes?: TopicNode[];
  subjectSlug: string;
  tone: "prereq" | "related" | "next";
}) {
  if (!nodes || nodes.length === 0) return null;
  const toneColor =
    tone === "prereq" ? "neutral" : tone === "next" ? "accent" : "success";
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-semibold uppercase tracking-wider text-ink-3">
        {label}
      </span>
      {nodes.map((n) => {
        const slug = n.slug || "";
        const subject = n.subject_slug || subjectSlug;
        const href = slug ? `/learn/${subject}/${slug}` : "#";
        return (
          <Link key={slug} href={href}>
            <Badge color={toneColor}>{n.title}</Badge>
          </Link>
        );
      })}
    </div>
  );
}

export function TopicGraph({
  subjectSlug,
  prerequisites,
  related,
  nextTopics,
}: {
  subjectSlug: string;
  prerequisites?: TopicNode[];
  related?: TopicNode[];
  nextTopics?: TopicNode[];
}) {
  const hasAny =
    (prerequisites?.length ?? 0) > 0 ||
    (related?.length ?? 0) > 0 ||
    (nextTopics?.length ?? 0) > 0;
  if (!hasAny) return null;
  return (
    <div className="space-y-2 rounded-xl border border-ink-2/15 bg-bg-2/40 p-4">
      <p className="text-xs uppercase tracking-wider text-ink-3">
        Learning path
      </p>
      <Group label="Prerequisites" nodes={prerequisites} subjectSlug={subjectSlug} tone="prereq" />
      <Group label="Related" nodes={related} subjectSlug={subjectSlug} tone="related" />
      <Group label="Up next" nodes={nextTopics} subjectSlug={subjectSlug} tone="next" />
    </div>
  );
}
