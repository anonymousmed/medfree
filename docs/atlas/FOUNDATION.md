# MEDFREE — Human Atlas Foundation

The Atlas is a **first-class system** and the **centerpiece** of the product — not an optional feature.

## Interaction model (MVP)

The `@medfree/atlas` viewer exposes the full set of controls via React Three Fiber:

- **Rotate / Pan / Zoom** — drei `OrbitControls`
- **Isolate / Highlight** — per-part selection with emissive highlight
- **Hide / Show** — toggle parts
- **Labels** — drei `Html` overlay labels, toggleable
- **Search** — `/api/atlas/search` backed by Postgres (name + synonyms)
- **Structure selection + info** — side-by-side panel (region + metadata + clinical)
- **Structure identification** — select and name structures

## Content model

Structures are the canonical nodes. Regions and systems are independent dimensions; a structure belongs to a region and a system. 3D models reference structures through `atlas_model_parts`.

```
anatomical_regions     → anatomical_structures → anatomical_relationships
anatomical_systems     → anatomical_structures
atlas_models           → atlas_model_parts → anatomical_structures
                       → atlas_annotations
                       → atlas_reviews
```

A structure's data model (`app/models/atlas.py`) covers: name, synonyms, region, system, attachments, relations, blood supply, nerve supply, function, variations, surface anatomy, clinical relevance, imaging/radiology, embryology, histology, related structures, and links to MCQs/viva/flashcards/references.

## Coverage plan

- **Systems:** skeletal, muscular, nervous, cardiovascular, respiratory, digestive, urinary, reproductive, endocrine, lymphatic, integumentary.
- **Regions:** upper limb, lower limb, thorax, abdomen, pelvis/perineum, head & neck, back, neuroanatomy.
- **Expansion later:** histology, embryology, radiology, pathology, imaging-based anatomy.

## Performance (primary = tablet/desktop, phone compatible)

- Progressive/lazy loading, LOD, compressed geometry/textures
- Load only the selected region — never the whole body at once
- Cache frequently used models
- Fallback 2D diagrams for weak devices

## Data records & review

Every structure and model carries a `status`/`review_status`. Nothing is published until reviewed:
`draft → rights check → medical review → quality review → approved → published` (see 3D_PIPELINE).
