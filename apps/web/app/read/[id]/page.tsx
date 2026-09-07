"use client";

import { useParams } from "next/navigation";
import { PdfReader } from "@/components/PdfReader";

export default function ReadPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <PdfReader resourceId={id} />
    </div>
  );
}
