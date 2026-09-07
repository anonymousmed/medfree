# MEDFREE — Build Progress

> Live status of the Agent build. Aligned to the master spec section 59 roadmap.
> **Restarted from Step 0** on a clean plan; builds run in batches of 5 with a combined audit after each batch.

## ✅ Done & verified

- **Steps 0–1 (Foundation / Database)** — see `AUDIT_Step0.md`, `AUDIT_Step1.md`
- **Steps 2–5 (Auth / Base UI / Learning Core / Atlas Foundation)** — see `AUDIT_Steps2345.md`
- **Steps 6–10 (Atlas Advanced / Resource Library / Admin / MCQ / Viva)** — see `AUDIT_Steps678910.md`
- **Steps 11–15 (Flashcards / Practicals / AI Study Assistant / Gamification / Ads & Announcements)** — see `AUDIT_Steps1115.md`
- **Steps 16–20 (Analytics / Security / Mobile-Performance+PWA / Content Expansion / Partnerships)** — see `AUDIT_Steps1620.md`

## 📡 Running live
- **Frontend:** port **3000** (Next.js dev, `data-theme` themes, Atlas R3F viewer, live data via proxy)
- **Backend:** port **8000** (FastAPI, seeded SQLite, `/docs` OpenAPI)
- `NEXT_PUBLIC_API_URL=/api` → proxied to backend; falls back to bundled mock data if unreachable.
- New routes: `/flashcards`, `/practicals`, `/assistant`, `/gamification`, `/partners`, `/profile`; `/` shows announcements + placement banner; `/admin` has Content/users, **Upload**, **Manage**, **Analytics & audit**, and **Partnerships** tabs.
- **PWA** enabled: `manifest.webmanifest`, service worker (`sw.js`, offline page, no `/api` caching), app icons.
- Backend **security**: audit logs, rate limiting (in-memory, Redis-swappable), security headers, file-type validation.

### Bug fixed this batch
SSR `base()` in `lib/api.ts` was missing the `/api` prefix (used `MEDFREE_API_URL` host root directly), so **server-rendered pages silently used mock data**. Fixed to append `/api`; SSR now loads real API data (verified: library rights badge, atlas systems, topic blocks all from DB).

## ✅ Final launch-enabling batch (new) — see `docs/AUDIT_final.md`
Built in a single pass, then fully audited. All build work is now feature-complete.

- **Storage abstraction** (`app/core/storage.py`) — provider-agnostic driver (local dev / S3-compatible prod) with `presign → confirm → serve`; `POST /storage/presign` admin 200 / student 403 / bad-ext 422; serve path verified via frontend proxy (200).
- **Embeddings engine** (`app/core/embeddings.py` + `retrieve_vector()` in `core/ai.py`) — deterministic hashed embeddings, prod-swappable to openai/sentence-transformers/pgvector; `POST /ai/index` admin-only; `/ai/ask` merges keyword-first + vector-recall; verified clinically accurate sources.
- **Reports** (`models/report.py`, `routes/reports.py`) — anonymous `POST /reports` → status `open`; admin resolve → 200; `ReportError` widget on learn + library.
- **Admin content** (`routes/admin_content.py`, `AdminContent`/`AdminUpload` components) — resource edit/archive, review queue, ads, books CRUD, admin upload (presign → PUT → confirm).
- **Profile** (`GET/PATCH /me/profile`, `ProfileEditor.tsx`, `/profile`) — course/year/university/country/language/goal.
- **SEO** — `robots.txt` + `sitemap.ts` (`/sitemap.xml` 0 B).
- **`AdminPortal`** tabbed: content / upload / manage / insights / partners.
- **Migration** `744117468f95` (reports + content_embeddings + profile); fresh DB = 46 tables.

## ✅ Post-final verification + content expansion (new) — see `docs/AUDIT_PostFinal.md`
Independent re-audit (not trusting the prior one). Fixed real issues:
- **Removed fabricated resource** (`example.com`) and **corrected OpenStax A&P rights** (CC BY-NC-SA 4.0, AI-ingestion prohibited → `ai_usage_status='false'`).
- **Curated rights-aware library** (`scripts/library_pack.py`): 11 verified resources across Anatomy/Physiology/Biochemistry, with correct licence, rights status, external-vs-host, and AI-ingestion flags. Books → chapters → topics wired.
- **Curriculum knowledge graph**: added `TopicLink` (prerequisite/related/next) + `difficulty`/`est_minutes` to Topic; migration `d021308bae4f`; 16 seeded edges; exposed via `/subjects/{s}/topics/{t}` and the topic page (`TopicGraph`).
- **Security hardening**: 200 MB upload limit (API + local driver); `serve_storage` now only serves public/published resources (404 otherwise).
- Optional doc note: OpenStax AI-ingestion caveat in `RIGHTS_MODEL.md`.

**Tests are now 61 passed** (55 + 2 knowledge-graph/library + 4 security). `tsc` 0 errors; `next build` 20 routes; migrations from zero → 46 tables; seed idempotent.

## 🔜 Next milestones (deployment — requires your credentials)
Scheduled build work is **complete**. Remaining is **deployment + optional production tuning**, pending real credentials:
- Managed **PostgreSQL** (`DATABASE_URL`) + object storage (`STORAGE_*`).
- **Supabase Auth** env (`AUTH_PROVIDER=supabase`, `SUPABASE_*`).
- Deploy **backend** (Render/Railway) + **frontend** (Vercel); wire `/api` proxy + `NEXT_PUBLIC_API_URL`.
- Optional `REDIS_URL` (distributed rate limiting) and real embeddings/LLM key.
- Run the **medical review gate** before promoting any clinical claim to authoritative (content seed is reference/practice material).

## ⚠️ Credentials required (from user)
`DATABASE_URL` · `SUPABASE_URL` + keys + JWT secret · `STORAGE_ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET` · optional `REDIS_URL`, `LLM_API_KEY`, `EMBEDDING_PROVIDER` · Vercel/Render/Railway tokens. Full list in `docs/AUDIT_final.md` §14.

## Commands
```bash
# backend
cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python -m scripts.seed_dev && uvicorn app.main:app --reload
# tests
python -m pytest ../../tests -q
# frontend
npm install --legacy-peer-deps && npm run dev:web
# production build
npm --workspace @medfree/web run build
```
