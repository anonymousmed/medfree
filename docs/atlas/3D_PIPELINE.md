# MEDFREE — 3D Asset Pipeline

```
SOURCE
  ↓ LICENSE CHECK            (rights record; review_required halts)
  ↓ DOWNLOAD IF PERMITTED
  ↓ CHECKSUM
  ↓ MODEL CLEANUP
  ↓ MESH OPTIMIZATION
  ↓ TEXTURE COMPRESSION
  ↓ LOD GENERATION
  ↓ GLB / glTF
  ↓ STRUCTURE MAPPING         (atlas_model_parts → anatomical_structures)
  ↓ ANNOTATIONS
  ↓ MEDICAL REVIEW
  ↓ PERFORMANCE TEST
  ↓ PUBLISH
```

## Guidance

1. **Prefer GLB/glTF.** Render with Three.js / React Three Fiber (WebGL; WebGPU where supported).
2. **Rights first.** BodyParts3D (CC BY-SA 2.1 JP), Wikimedia Commons, and any NIH 3D assets must be license-checked and attributed. Never assume reusability from online availability.
3. **Optimize for the primary device.** Tablets/desktops get richer budgets; phones get LOD + 2D fallback.
4. **Load lazily.** Only the selected region loads; never the whole body at once.
5. **Structure mapping is the key step.** Each mesh maps to an `anatomical_structure` so selection, labels, quizzes and viva all resolve.
6. **Review before publish.** Each model passes medical/quality review (admin panel preview included).

## Format targets
- Quality: LOD 0–3
- Geometry: compressed
- Textures: compressed (e.g. KTX2/WebP)
- Mesh size budget per region vs. budget per whole body documented at test time
