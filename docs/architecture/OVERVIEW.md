# MEDFREE — Architecture Overview

## 1. Product architecture (Atlas-first)

```
                            ┌──────────────────────────────────────────────┐
                            │   FRONTEND  ·  Next.js (apps/web)  ·  Vercel   │
                            │                                               │
                            │  AppShell (sidebar/topbar/bottom-nav)          │
                            │  ThemeProvider (dark/light/midnight/oled)      │
                            │  Pages: Home · Atlas · Learn · Practice ·      │
                            │         Library · Progress · Auth              │
                            │  AtlasViewer (@medfree/atlas, R3F + drei)      │
                            └───────────────┬───────────────────────────────┘
                                            │  /api/* (proxied)
                                            ▼
                            ┌──────────────────────────────────────────────┐
                            │   BACKEND  ·  FastAPI (apps/api) · Render/Ry  │
                            │                                               │
                            │  Auth (Supabase / mock)  →  RBAC deps          │
                            │  Routers: health · auth · atlas · subjects ·   │
                            │            resources · admin                   │
                            │  Admin-only upload enforced at the dependency  │
                            │  layer (403 for students/contributors)         │
                            └───────────────┬───────────────────────────────┘
                       ┌────────────────────┼───────────────────────────────┐
                       ▼                    ▼                               ▼
            ┌──────────────────┐  ┌───────────────────┐          ┌────────────────┐
            │ Managed Postgres │  │ S3-compatible     │          │ Redis / Workers│
            │ (+ pgvector for  │  │ object storage    │          │ (caching, jobs,│
            │  AI/RAG)         │  │ books/3D/media    │          │ rate limiting) │
            └──────────────────┘  └───────────────────┘          └────────────────┘
```

## 2. ER diagram (core entities)

```
users ──< user_roles >── (roles.RBAC)
  │
  ├──< subjects ──< topics
  │                      │
  │                      └──< (topic ↔ book_chapters mapping)
  │
  ├──< resources ──< resource_versions
  │        │
  │        ├──> licenses (rights)
  │        ├──> books ──< book_chapters
  │        └──> authors
  │
  ├──< atlas (region/system/structure graph)
  │        anatomical_regions
  │        anatomical_systems
  │        anatomical_structures ──< anatomical_relationships (structure_a/b)
  │        atlas_models ──< atlas_model_parts
  │                     ──< atlas_annotations
  │                     ──< atlas_reviews
  │
  ├──< questions ──< question_options
  ├──< viva_questions
  ├──< flashcards
  └──< practicals
```

## 3. Tech selection

| Concern | Choice | Why |
|---|---|---|
| Frontend | **Next.js 14 + TS + Tailwind** | SSR/SSG, strong ecosystem, Vercel-native |
| Backend | **FastAPI + SQLAlchemy 2 async** | Fast, typed, Pydantic-integrated |
| Database | **managed PostgreSQL + pgvector** | relational core + vector AI/RAG later |
| Auth | **Supabase** (abstraction) | managed; provider swappable |
| Storage | **S3-compatible** (abstraction) | portable, cheap object storage |
| 3D | **Three.js / React Three Fiber** | industry standard, GLB/glTF |
| Hosting | **Vercel + Render/Railway** | no VPS; managed free tiers for MVP |
| Cache/queues | **managed Redis** | optional, on-demand |

## 4. Design principles

1. **Centerpiece first** — Atlas leads the IA; books are the reference layer.
2. **RBAC by default at the backend** — hiding UI is never a security control.
3. **Right-aware library** — every resource carries a rights record; `review_required` blocks publish.
4. **Modular monolith** — no microservices/Kubernetes initially; scale later.
5. **Provider-agnostic** — thin abstractions for DB, storage, auth and hosting so they can be swapped.
6. **₹0 MVP, honest scaling** — free tiers for MVP; real costs acknowledged as the platform grows.

See [CLOUD.md](CLOUD.md) for the deployment architecture.
