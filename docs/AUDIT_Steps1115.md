# MEDFREE — Combined Audit Report: Steps 11–15

> Batch build following the re-sequenced roadmap. Steps 0–1, 2–5 and 6–10 already audited & accepted.
> Product direction preserved: **Tablet/Desktop-first**, **Human Atlas = centerpiece**, **books = knowledge/reference layer**, **admin-only upload enforced at the backend**.
> This batch closes the **Study / Active-Recall** phase: Flashcards, Practicals, AI Study Assistant (RAG), Gamification, and the Ads/Announcements platform.

---

## Step 11 — Flashcards (spaced repetition) ✅
**Backend** (`apps/api/app/api/routes/flashcards.py`)
- `GET /flashcards` — list/filter by `subject` & `topic`.
- `GET /flashcards/stats` — `total_cards`, `due_now`, `reviewed`, `average_interval_days` (per user).
- `GET /flashcards/due` — cards due **for this user** (never reviewed **OR** `due_at <= now`).
- `POST /flashcards/{id}/review` — SM-2-inspired schedule. **Transparent, deterministic, no FSRS** (documented as an upgrade path).

**Spaced-repetition correctness (verified live):**
| Review | Quality | Interval |
|---|---|---|
| 1st | 5 | 1 day |
| 2nd | 5 | 6 days |
| 3rd | 5 | ~17 days (interval × ease, ease starts 2.5, floor 1.3) |
| any | < 3 | **reset to 1 day** |

Ease update: `EF = max(1.3, EF + (0.1 − (5−q)(0.08 + (5−q)·0.02)))`. Intervals for review_count 1→1d, 2→6d, else `round(interval × ease)`.

**Frontend** (`/flashcards`): subject tabs, Review-due vs Browse-all toggle, tap-to-flip card, quality grading buttons (Again/Hard/Good/Easy/Perfect), live stats cards, per-card scheduled interval feedback.

## Step 12 — Practicals (checklists / spotters) ✅
**Backend** (`apps/api/app/api/routes/practicals.py` + `app/models/practice.py`)
- `Practical` enriched with teaching fields: `topic_slug`, `requirements`, `principle`, `preparation`, `observation`, `interpretation`, `common_mistakes`, `safety_notes`, `clinical_significance`, `reference_text`.
- New `PracticalStep` model (`position`, `step_text`, `observation`), eager-loaded with the parent.
- `GET /practicals` (filter by subject, published only), `GET /practicals/{id}` (all teaching fields + `steps[]` sorted by `position`).

**Frontend** (`/practicals`): subject filter, card grid, detail view with numbered step-by-step procedure, and Safety / Clinical significance / Common-mistakes panels.

## Step 13 — AI Study Assistant (RAG) ✅
**Backend** (`apps/api/app/core/ai.py` + `app/api/routes/ai.py`)
- `POST /ai/ask` → `{ answer, sources:[{source_type,source_id,title,href}], disclaimer }`.
- `GET /ai/ingestion-policy` → explains eligibility; both `unknown_is_excluded` and `review_required_is_excluded` are `true`.

**Content-eligibility gate (the critical safety property):**
- `is_ingestable()` returns `True` **only** when `ai_usage_status.strip().lower() == "true"`.
- `retrieve()` queries only resources where `ai_usage_status == 'true'`, `rights_status NOT IN ('review_required','blocked','external_only')`, and `visibility == 'public'`.
- Atlas structures are restricted to `status == 'verified'`; topic blocks only from published topics.
- **Never ingests `unknown` or `review_required` content** (verified in tests + policy endpoint).

**Retrieval & ranking:** provider-agnostic. With pgvector + embeddings it would use vector similarity; in local/CI it falls back to keyword overlap. Within the fallback, topics are ranked by **title+summary** first, then the **best explanatory block** per topic is kept (overview/clinical/diagram weighted 1.0; mcq/viva/flashcards weighted 0.4), and the answer builder **deduplicates identical text and skips bare quiz prompts** so the result reads like an explanation, not a test. Answer generation is a deterministic, retrieval-grounded builder (no external LLM/key required), swappable for an LLM behind the same contract.

**Frontend** (`/assistant`): question box, suggested prompts, citation list, policy badge, answer + disclaimer.

## Step 14 — Gamification (non-childish, real activity) ✅
**Backend** (`apps/api/app/core/gamification.py` + models in `app/models/gamification.py`)
- `GET /gamification/summary` → `{ streak:{current,longest}, xp, level, quiz_attempts, quiz_accuracy, topics_completed, badges[] }`.
- **Derived from real study activity** (never fabricated): XP = `quiz_correct*10 + viva_total*5 + flashcard_total*3 + topics_completed*20`.
- `xp_level = (xp // 100) + 1`.
- **Idempotent & auditable:** recomputes the target XP on each call and records only the **delta** as an `XPTransaction(reason='activity_sync')`, and only inserts **new** badges (never re-awards). No fixed/random childlike rewards.
- Badges: `first_topic`, `viva_starter`, `first_revision`, `mcq_100`, `mcq_500`, `streak_7`, `streak_30`, `subject_master`.

**Idempotency verified live:** calling `/gamification/summary` 3× in a row kept `xp=6` and `badges=1` (no growth). Streak updates only when `last_active_on != today` and advances by 1 for consecutive days (resets to 1 after a >1-day gap).

**Frontend** (`/gamification` / `/progress`): streak/XP/level stats, progress-to-next-level bar, badge grid, activity mini-stats.

## Step 15 — Advertisement / Monetization + Announcements ✅
**Backend** (`apps/api/app/api/routes/platform.py` + `app/models/content_platform.py`)
- **Public reads** (active + in-schedule only):
  - `GET /ads?placement=` → highest-priority active ad for the placement, `null` if none. Only `is_active` and within `start_at`/`end_at` window.
  - `GET /announcements` → up to 5 active, in-schedule, newest first.
- **Admin-only writes** (behind `require_admin`):
  - `POST /admin/ads`, `PATCH /admin/ads/{id}`, `DELETE /admin/ads/{id}`.
  - `POST /admin/announcements`.

**Placement safety:** ads are **admin-controlled** (placement/priority/start/end/is_active) and only public routes ever serve them; no student/community content can become an ad. No deceptive/unlabeled placements — public banner always carries the title/target and alt-text.

**Frontend**: `HomepageBanner` on `/` (dismissable announcements + controlled placement banner), and an **Announcements & Advertisement placement** panel in `AdminPortal` (admin-only).

---

## Detailed Audit

### Backend tests
- **`python -m pytest -q` → 34 passed** ✅ (24 from Steps 0–10 + 10 new)
  - Steps 0–10 regressions all green (health, RBAC upload enforcement, auth identity, learning blocks, bookmarks, notes, Atlas advanced, library/search, admin, MCQ, viva).
  - New `tests/test_steps11to15.py` covers: flashcard list/stats, flashcard review updates due & interval, practicals detail-with-steps ordering, practicals list filtering by subject + published-only, AI ingestion-policy (unknown/review_required excluded), AI ask returns cited sources, gamification summary shape, gamification awards XP + first_topic badge after completing a topic, public banner & announcement, and **admin-only ad write (student → 403, content_admin → 201)**.

### Frontend build
- **`npm install` (root) + `tsc --noEmit` → 0 errors** ✅
- **`next build` → success** ✅ (17 routes). New routes: `/flashcards`, `/practicals`, `/assistant`, `/gamification`, plus updated `/` (banner) & `/admin` (platform panel).

### API smoke tests (live, via `/api` proxy)
- `GET /flashcards?subject=` ✅, `GET /flashcards/stats` ✅, `GET /flashcards/due` ✅, `POST /flashcards/{id}/review` ✅
- `GET /practicals?subject=` ✅, `GET /practicals/{id}` (steps + teaching fields) ✅
- `POST /ai/ask` → answer + sources[] + disclaimer ✅; `GET /ai/ingestion-policy` ✅
- `GET /gamification/summary` ✅
- `GET /announcements` ✅, `GET /ads?placement=homepage` ✅
- `POST /admin/ads` (content_admin) → 201 ✅; (student) → **403** ✅; `POST /admin/announcements` ✅

### RBAC / admin-only enforcement (mandate #4 / #10)
| Actor | `POST /admin/ads` | `POST /admin/announcements` |
|---|---|---|
| Student | **403** ✅ | **403** ✅ |
| Content Admin | **201** ✅ | **201** ✅ |

Step 13 gate is separate from RBAC but equally hard: no role — not even admins — can make `ai_usage_status='unknown'` or `rights_status='review_required'` content ingestible; `is_ingestable()` returns `False` for both.

### Spaced-repetition correctness
SM-2-inspired intervals verified via HTTP (see table in Step 11). Ease floor 1.3, quality<3 resets to 1 day. Transparent & deterministic (documented; no hidden FSRS). No test flakiness across repeated calls.

### Gamification idempotency & correctness
- XP strictly derived from counts; only the **delta** is recorded as an auditable `XPTransaction`.
- Badges inserted only once (not re-awarded); repeated summary calls produce **identical** results.
- Streak resets after a >1-day gap (verified logic; unit-level assert on reset path).

### Ad / announcement placement
- Public endpoints serve only `is_active` + in-schedule items.
- Admin CRUD is backend-gated; public never serves draft/expired content.

### Security
- RBAC enforced at backend dependencies (`require_admin`), not hidden UI.
- AI eligibility gate enforced in `retrieve()`/`is_ingestable()` (defense in depth: even if the UI said "ask", only approved content is retrieved).
- No external LLM call with secrets in dev/CI; answer builder is deterministic.
- Auth abstraction (mock ↔ Supabase) retained; no secrets committed.

### Database migrations
- **7 new tables:** `ads`, `announcements`, `gamification_events`, `practical_steps`, `user_badges`, `user_streaks`, `xp_transactions`.
- Migration `1240b46aa684_practicals_gamification_ads_.py` autogenerated & applied; fresh DB (`rm -f medfree.db && alembic upgrade head`) → **39 tables**, new tables present.
- Migration head is now `1240b46aa684`. Lineage: `6e86f8b978f5` → `de453e237e0d` (learning blocks) → `1240b46aa684` (7 tables). (The earlier no-op head `655142baa9cd` is no longer head.)

### Regressions from Steps 0–10
- **None.** 34/34 tests pass; `import app.main` OK; all prior routes still invoked in smoke tests.
- Two refinements (non-regressing): practicals seed was converted to an **upsert** so pre-existing rows get enriched teaching fields + steps; AI retrieval ranked to avoid quiz-prompt noise.

---

## Notes / decisions
- **FSRS deferred:** SM-2-inspired intervals are transparent and testable; an FSRS implementation can be swapped behind the same `POST /flashcards/{id}/review` contract without UI/API breakage.
- **No external LLM required** for Step 13 in dev/CI — retrieval-grounded deterministic builder keeps the feature offline-capable and honest; a real model can be plugged into `build_answer` later.
- **Gamification is non-childish** — XP/badges/streaks map 1:1 to real quiz/viva/flashcard/progress counts; no arbitrary currency or gacha.

---

## Next batch
**Beyond this batch:** signed-URL object-storage uploads; pgvector + embeddings for Step 13 vector retrieval; PWA + responsive/Atlas perf test; content expansion + rights review per `docs/content/SOURCES.md`; live deployment (Vercel + Render/Railway + managed Postgres/S3/Redis).

---

*Generated by the MEDFREE build agent. End of Steps 11–15 combined audit.*
