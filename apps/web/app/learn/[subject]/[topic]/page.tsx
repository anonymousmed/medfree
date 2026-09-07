import { Badge } from "@medfree/ui";
import { fetchTopicBlocks } from "@/lib/api";
import { TopicFlow } from "@/components/TopicFlow";
import { TopicGraph } from "@/components/TopicGraph";
import { ReportError } from "@/components/ReportError";

export default async function TopicPage({
  params,
}: {
  params: { subject: string; topic: string };
}) {
  const topic = await fetchTopicBlocks(params.subject, params.topic);
  const blocks = (topic.blocks ?? []).sort((a, b) => a.position - b.position);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Badge color="accent">{params.subject}</Badge>
            {topic.difficulty && (
              <Badge color="neutral">{topic.difficulty}</Badge>
            )}
          </div>
          <h1 className="mt-2 text-3xl font-bold">{topic.title}</h1>
          {topic.summary && <p className="mt-1 max-w-2xl text-ink-2">{topic.summary}</p>}
        </div>
        <ReportError target_type="topic" target_slug={params.topic} />
      </div>

      <p className="text-xs uppercase tracking-wider text-ink-3">
        Learn → Explore → Practice → Master
      </p>

      <TopicGraph
        subjectSlug={params.subject}
        prerequisites={topic.prerequisites}
        related={topic.related}
        nextTopics={topic.next_topics}
      />

      <TopicFlow
        subjectSlug={params.subject}
        topicSlug={params.topic}
        blocks={blocks}
        initialMastery={topic.mastery ?? 0}
      />
    </div>
  );
}
