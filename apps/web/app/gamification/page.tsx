import { GamificationClient } from "@/components/GamificationClient";

export const metadata = { title: "Rewards — MEDFREE" };

export default function GamificationPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <GamificationClient />
    </div>
  );
}
