import { PracticalsClient } from "@/components/PracticalsClient";

export const metadata = { title: "Practicals — MEDFREE" };

export default function PracticalsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PracticalsClient />
    </div>
  );
}
