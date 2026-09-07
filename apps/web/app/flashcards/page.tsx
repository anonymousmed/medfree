import { FlashcardsClient } from "@/components/FlashcardsClient";

export const metadata = { title: "Flashcards — MEDFREE" };

export default function FlashcardsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <FlashcardsClient />
    </div>
  );
}
