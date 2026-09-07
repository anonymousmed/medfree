import type { TopicBlock, TopicDetailWithBlocks } from "@medfree/types";

/** Bundled structured learning blocks for the brachial plexus (fallback). */
export const MOCK_TOPIC_BLOCKS: TopicDetailWithBlocks = {
  id: 1,
  slug: "brachial-plexus",
  title: "Brachial Plexus",
  summary: "Roots, trunks, divisions, cords and branches forming the nerve supply of the upper limb.",
  blocks: [
    { id: 1, position: 0, block_type: "overview", title: "Quick Overview", content: "A network of nerves supplying the upper limb, formed by the ventral rami of C5–T1. It passes from the neck, through the axilla, to the upper limb." },
    { id: 2, position: 1, block_type: "objectives", title: "Learning Objectives", content: "Name the roots, trunks, divisions, cords and branches.\nDescribe the course from spinal cord to upper limb.\nRelate clinical lesions (Erb's, Klumpke's) to specific parts." },
    { id: 3, position: 2, block_type: "atlas", title: "Human Atlas / 3D", content: "Explore this structure in the interactive 3D Human Atlas.", meta: '{"type":"atlas","region":"upper-limb","structure":"brachial-plexus"}' },
    { id: 4, position: 3, block_type: "diagram", title: "Interactive Diagram", content: "Roots → Trunks → Divisions → Cords → Branches. Toggle each level to build the plexus step by step." },
    { id: 5, position: 4, block_type: "clinical", title: "Clinical Correlation", content: "Erb's palsy (C5–C6) → waiter's tip position. Klumpke's palsy (C8–T1) → claw hand." },
    { id: 6, position: 5, block_type: "mcq", title: "MCQs", content: "Attempt questions on the brachial plexus.", meta: '{"type":"mcq","topic":"brachial-plexus"}' },
    { id: 7, position: 6, block_type: "viva", title: "Viva", content: "Practice oral exam questions with model answers.", meta: '{"type":"viva","topic":"brachial-plexus"}' },
    { id: 8, position: 7, block_type: "flashcard", title: "Flashcards", content: "Spaced-repetition cards for active recall.", meta: '{"type":"flashcard","topic":"brachial-plexus"}' },
    { id: 9, position: 8, block_type: "books", title: "Books & Research", content: "OpenStax Anatomy & Physiology, Gray's Anatomy for Students, NCBI Bookshelf." },
    { id: 10, position: 9, block_type: "revision", title: "Revision", content: "Quick recap: C5–T1 → trunks → divisions → cords → branches." },
  ] as TopicBlock[],
};
