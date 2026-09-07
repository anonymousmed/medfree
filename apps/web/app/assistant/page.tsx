import { AssistantClient } from "@/components/AssistantClient";

export const metadata = { title: "AI Study Assistant — MEDFREE" };

export default function AssistantPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <AssistantClient />
    </div>
  );
}
