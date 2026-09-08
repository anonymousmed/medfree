import type { Metadata } from "next";
import Link from "next/link";
import { Badge, SectionHeading } from "@medfree/ui";
import { DetailedAtlasViewer } from "./viewer";

// The ashemag/human-atlas demo is an MIT-licensed app over CC BY 4.0 BodyParts3D
// anatomy data. MEDFREE embeds/link-outs to it as a legally permitted external
// resource (attribution preserved), mirroring the external-only library policy.
export const metadata: Metadata = {
  title: "Detailed Human Atlas",
  description:
    "High-resolution 3D anatomy explorer with 2,234 selectable BodyParts3D meshes, system layers, search and exploded views.",
};

const DETAILED_ATLAS_URL = "https://human-atlas-seven.vercel.app/";

export default function DetailedAtlasPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <SectionHeading
        eyebrow="Human Atlas · Deep dive"
        title="Detailed Human Atlas"
        subtitle="A high-resolution, fully selectable 3D anatomy explorer — 2,234 BodyParts3D meshes, system layers, search, and exploded views."
      />

      <div className="flex flex-wrap items-center gap-3">
        <Link
          href={DETAILED_ATLAS_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
        >
          Open Detailed Atlas ↗
        </Link>
        <a href={DETAILED_ATLAS_URL} target="_blank" rel="noopener noreferrer">
          <Badge color="success">Legal · CC BY 4.0</Badge>
        </a>
        <Badge color="neutral">2,234 meshes</Badge>
      </div>

      <div className="space-y-2 rounded-xl border border-ink-2/15 bg-bg-2/40 p-4 text-sm text-ink-2">
        <p>
          <strong>About this 3D asset:</strong> the detailed explorer is the open-source{" "}
          <a
            href="https://github.com/ashemag/human-atlas"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            ashemag/human-atlas
          </a>{" "}
          app (MIT licensed) over{" "}
          <a
            href="https://github.com/Kevin-Mattheus-Moerman/BodyParts3D"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            BodyParts3D
          </a>{" "}
          anatomy data (<strong>CC BY 4.0</strong> — attribution preserved).
        </p>
        <p>
          MEDFREE links to this legally permissive external resource; it is not a downloaded/rebundled copy.
          Use it alongside MEDFREE&apos;s own structure database, topic relationships, progress and review.
        </p>
      </div>

      {/* Embedded live viewer with fullscreen + tall-view controls. In
          restricted/offline previews it shows the shell; use the external
          button above to open it directly. */}
      <DetailedAtlasViewer />
    </div>
  );
}
