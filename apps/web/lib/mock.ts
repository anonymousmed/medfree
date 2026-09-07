import type { AtlasRegion, AtlasStructure, Subject, TopicDetail } from "@medfree/types";

/** Bundled fallback data so pages render even when the API is offline. */

export const MOCK_REGIONS: AtlasRegion[] = [
  { id: 1, slug: "upper-limb", name: "Upper Limb" },
  { id: 2, slug: "thorax", name: "Thorax" },
  { id: 3, slug: "abdomen", name: "Abdomen" },
  { id: 4, slug: "head-neck", name: "Head & Neck" },
  { id: 5, slug: "neuroanatomy", name: "Neuroanatomy" },
];

export const MOCK_STRUCTURES: AtlasStructure[] = [
  {
    id: 1,
    preferred_name: "Brachial Plexus",
    latin_name: "Plexus brachialis",
    synonyms: "Brachial plexus",
    region_id: 1,
    system_id: 1,
    description:
      "Network of nerves supplying the upper limb. Formed by the ventral rami of C5–T1.",
    clinical_notes: "Erb's palsy results from injury to C5–C6 roots; Klumpke's from C8–T1.",
  },
  {
    id: 2,
    preferred_name: "Median Nerve",
    latin_name: "Nervus medianus",
    synonyms: "Median nerve",
    region_id: 1,
    description: "Mixed nerve of the upper limb; supplies most forearm flexors and thenar muscles.",
    clinical_notes: "Carpal tunnel syndrome compression; 'hand of benediction' on high lesion.",
  },
  {
    id: 3,
    preferred_name: "Brachial Artery",
    latin_name: "Arteria brachialis",
    region_id: 1,
    description: "Main artery of the arm; continuation of the axillary artery at teres major.",
    clinical_notes: "Pulse feelable in the cubital fossa; used for blood pressure measurement.",
  },
  {
    id: 4,
    preferred_name: "Axilla",
    latin_name: "Axilla",
    region_id: 1,
    description: "Pyramidal space containing the axillary vessels and brachial plexus.",
  },
];

export const MOCK_SUBJECTS: Subject[] = [
  { id: 1, slug: "anatomy", title: "Anatomy", description: "Gross & regional anatomy with the Human Atlas.", color: "#f0abfc" },
  { id: 2, slug: "physiology", title: "Physiology", description: "How the body works — simulations & practicals.", color: "#38bdf8" },
  { id: 3, slug: "biochemistry", title: "Biochemistry", description: "Pathways, reactions and clinical correlations.", color: "#4ade80" },
];

export const MOCK_TOPICS: TopicDetail[] = [
  {
    id: 1,
    slug: "brachial-plexus",
    title: "Brachial Plexus",
    summary: "Roots, trunks, divisions, cords and branches forming the nerve supply of the upper limb.",
    mastery: 72,
  },
  {
    id: 2,
    slug: "femoral-triangle",
    title: "Femoral Triangle",
    summary: "Boundaries and contents — the femoral nerve, artery and vein.",
    mastery: 41,
  },
  { id: 3, slug: "median-nerve", title: "Median Nerve", summary: "Course, branches and clinical lesions.", mastery: 55 },
];
