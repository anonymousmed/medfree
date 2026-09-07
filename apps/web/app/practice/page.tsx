import { SectionHeading } from "@medfree/ui";
import { PracticeHub } from "@/components/PracticeHub";

export default function PracticePage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionHeading
        eyebrow="Practice"
        title="Practice & Active Recall"
        subtitle="MCQs and viva tied to every topic, with instant explanations."
      />
      <PracticeHub />
    </div>
  );
}
