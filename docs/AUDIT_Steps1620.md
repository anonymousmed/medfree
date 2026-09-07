# MEDFREE — Combined Audit Report: Steps 16–20

> Batch build following the re-sequenced roadmap (§59). Steps 0–1, 2–5, 6–10 and 11–15 already audited & accepted.
> Product direction preserved: **Tablet/Desktop-first**, **Human Atlas = centerpiece**, **books = knowledge/reference layer**, **admin-only upload enforced at the backend**.
> This batch closes the **Platform & Scale** phase: Analytics, Security, Mobile/Performance + PWA, Content Expansion, and Partnerships.

---

## Step 16 — Analytics ✅
**Backend** (`apps/api/app/models/analytics.py`, `app/api/routes/analytics.py`)
- **Non-invasive product & learning analytics.**
- `POST /analytics/events` — record a product/learning event (`page_view`, `atlas_open`, `quiz_start`, …). **Works anonymously** (optional `user_id`); captures no personal data beyond what the product already knows.
- `POST /analytics/search` — record a search interaction for search analytics (`is_failed` auto-set when `result_count==0`).
- `GET /admin/analytics` — on-demand aggregates (no OLAP at MVP scale): total/active/new users, topics completed, quiz attempts & accuracy, **search volume + failed searches + top queries**, most-used Atlas structures, most-engaged topics.

**Frontend** (`AdminInsights` in admin panel): stat cards, learning & search analytics, top-queries list.

## Step 17 — Security ✅
**Backend** (`apps/api/app/core/security.py`, `app/api/routes/security.py`, `app/models/security.py`)
- **`audit_logs`** model + `record_audit()` helper. Every privileged mutation now writes an audit row with actor, action, target, detail, IP, result:
  - `resource.review` (approve/reject/publish), `resource.publish` gate preserved (rights-required → 422)
  - `user.role_change`, `atlas.model_ingest`, `ad.create`, `announcement.create`
  - `GET /admin/audit-logs` read side for the admin panel.
- **Rate limiting** (`rate_limit()`), provider-agnostic: in-memory windows (dev/CI) with a Redis-swappable interface. Applied to search, auth identity, and admin mutations. Configurable via `settings.rate_limit_*`.
- **Security headers middleware** applied to every response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-XSS-Protection`, `Permissions-Policy` (camera/mic/geolocation off), `Cross-Origin-Opener-Policy: same-origin`.
- **File-type validation** `validate_upload_type()` (allowlist per resource type; rejects `.exe` etc.).

**Frontend** (`AdminInsights`): recent privileged-action audit trail with success/fail badges.

## Step 18 — Mobile / Performance + PWA ✅
**Frontend** (`apps/web/public/*`, `app/layout.tsx`)
- **PWA manifest** (`manifest.webmanifest`): name, icons, shortcuts (Atlas, Practice), theme/background colors, display standalone.
- **Service worker** (`sw.js`): app-shell caching, network-first navigations with offline shell fallback, **never caches `/api/*`** (correctness over stale medical content). Registered in `RootLayout`.
- **Offline page** (`offline.html`) with graceful reconnect message.
- **Icons** (`icon-192.svg`, `icon-512.svg`).
- **Metadata**: `manifest`, `appleWebApp`, `icons`, viewport `viewportFit: cover` for edge-to-edge mobile.
- **Performance**: the heavy Atlas/R3F viewer already uses `dynamic()` (code-splitting); no new heavy route added to the critical path. All new routes are static (`○`) except `/partners` which is also static SSR.

## Step 19 — Content Expansion ✅
**Seed** (`apps/api/scripts/content_pack.py`, `scripts/seed_content.py`) — data-driven, idempotent (keyed by stable name/stem/prompt/front).
- **Structures** 5 → **29** across upper limb, thorax, abdomen, head & neck, neuroanatomy (with region/system mapping, description + clinical notes).
- **Topics** 3 → **14** (axilla, shoulder, thoracic cage, inguinal region, cardiac cycle, respiratory physics, renal physics, nerve conduction, glycolysis, Krebs, protein synthesis, …), each with the full **11-block structured learning flow** (overview → objectives → atlas → diagram → clinical → MCQ → viva → flashcards → practical → books → revision). Blocks 33 → **154**.
- **Questions** 3 → **14** (with options, correct index, explanation), **viva** 3 → **11**, **flashcards** 4 → **15**, **practicals** 2 → **5** (with step-by-step procedures).

## Step 20 — Partnerships ✅
**Backend** (`apps/api/app/models/partnership.py`, `app/api/routes/partnerships.py`)
- `institutions` (directory entry) + `partnership_requests` (interest queue).
- Public: `GET /partners` (active, featured-first directory), `POST /partners/interest` (visitor submission → queued `pending`).
- Admin (RBAC): `GET/POST /admin/partners`, `PATCH /admin/partners/{id}` (feature/activate/deactivate), `GET /admin/partnership-requests`, `PATCH /admin/partnership-requests/{id}` (reviewing/accept/decline).
- **No visitor-submitted interest is ever auto-published** — it always enters the review queue (spec §37).

**Frontend**: public `/partners` page (directory + partnership interest form) and **Partnerships** tab in the admin panel.

---

## Detailed Audit

### Backend tests
- **`python -m pytest -q` → 45 passed** ✅ (34 from Steps 0–15 + 11 new)
  - New `tests/test_steps16to20.py`: anonymous event tracking, search analytics + admin aggregate, admin analytics requires admin (403), audit log recorded on role change, audit log requires admin (403), security headers present, `validate_upload_type` (accepts `.pdf`, rejects `.exe`), rate-limit triggers **429**, partnership interest submit, public partner directory + admin create/patch, partnership admin requires admin (403).
  - A cross-test rate-limit leak was found during testing (shared in-memory bucket keyed on the test host). Fixed by adding `clear_rate_limits()` and an autouse conftest fixture that resets it between tests.

### Frontend build
- **`tsc --noEmit` → 0 errors** ✅
- **`next build` → success** ✅ (18 routes). New: `/partners`; admin panel now has Analytics & audit + Partnerships tabs.

### API smoke tests (live, via `/api` proxy)
- `POST /analytics/events` (anonymous) → 201 ✅; `POST /analytics/search` ✅
- `GET /admin/analytics` → aggregate (users, search volume/failed/top-queries) ✅; student → **403**/401 ✅
- `GET /admin/audit-logs` → rows ✅; student → **403** ✅
- Security headers on `/api/health` direct **and** proxied through `:3000` ✅
- Rate limit on `GET /search` → **429** after budget ✅
- `GET /partners`, `POST /partners/interest` ✅; `GET/POST/PATCH /admin/partners`, `PATCH /admin/partnership-requests/{id}` ✅; student → **403** ✅

### RBAC / security enforcement (mandate #7, §9)
| Actor | `GET /admin/analytics` | `GET /admin/audit-logs` | `POST /admin/partners` |
|---|---|---|---|
| Student | **403** ✅ | **403** ✅ | **403** ✅ |
| Content Admin | **200** ✅ | **200** ✅ | **201** ✅ |

### Security
- RBAC enforced at backend dependencies (`require_admin`), not hidden UI.
- Security headers on all responses; rate limits on search/auth/admin.
- Audit trail for privileged mutations (upload/review/publish/role/ad/announcement/model) — supports compliance & backups (spec §49, §51).
- File-type allowlist validation on upload paths (no arbitrary executables).
- PWA service worker deliberately does **not** cache `/api/*` to avoid serving stale medical content offline.

### Rate limiting
- In-memory window keyed by client IP / optional user id. Interface abstracts to Redis (`REDIS_URL`) for multi-instance, with a `_RedisRateLimiter` placeholder. Verified 429 fires after the configured budget for search.

### PWA / mobile / performance
- Manifest + SW + offline page + icons + metadata registered. Service worker install/activate/fetch logic validated (no `/api` caching). Heavy Atlas viewer remains code-split via `next/dynamic`.

### Spaced-repetition / gamification / AI regressions
- Steps 11–15 features untouched and still green (flashcards SM-2, gamification idempotency, Step 13 AI eligibility gate). No behavioural regressions; all prior routes invoked via smoke/proxy tests.

### Database migrations
- **5 new tables:** `analytics_events`, `search_events`, `audit_logs`, `institutions`, `partnership_requests`.
- Migration `61378de8dd44_analytics_security_partnerships.py` autogenerated & applied; fresh DB (`rm -f medfree.db && alembic upgrade head`) → **44 tables** (was 39).
- Migration head: `61378de8dd44`. Lineage: `6e86f8b978f5` → `de453e237e0d` → `1240b46aa684` → `61378de8dd44`.

### Regressions from Steps 0–15
- **None.** 45/45 tests pass; all prior features green.

---

## Notes / decisions
- **Analytics is non-invasive & on-demand** — no OLAP, no external analytics SDK in dev. Aggregates are computed from existing tables; events are anonymous where possible.
- **Rate limiting and audit are provider-agnostic** (Redis-swappable; in-memory default) so they run in local/CI and scale to managed Redis in production.
- **PWA caches the app shell only** — never medical/API data — so offline shows a friendly shell without risking stale clinical content.
- **Content expansion is curated and non-authoritative** — it must still pass medical review before any clinical claim is definitive (spec §55, §72). Marked as content for review, not treated as authoritative.
- The codebase uses the existing `Optional[X]` typing convention; ruff's new `X | None` suggestions are cosmetic and were intentionally not applied to keep style consistent with the rest of the models.

---

## Next batch
The roadmap steps 16–20 are now complete. Remaining programme-level work (not roadmap "steps" but required for launch):
- **Object-storage uploads** (signed URLs + admin metadata/rights form) — finishes the admin content-management layer the Cloud doc references, and closes the §63 ingestion pipeline.
- **pgvector + embeddings** for Step 13 vector retrieval.
- **Live deployment** (Vercel + Render/Railway + managed Postgres/object storage/Redis) using `docs/deployment/CLOUD.md` — requires the credentials listed below.
- **Medical review** of expanded content before any clinical claim is authoritative.

---

## Credentials / env needed for production (not required for this build — used mock/mocks so everything works locally)

| Env var | Purpose | Notes |
|---|---|---|
| `AUTH_PROVIDER=supabase`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY` | Auth | Backend JWT verification + service-role for admin ops |
| `DATABASE_URL` | Managed Postgres | `postgresql+asyncpg://…` |
| `STORAGE_ENDPOINT` / `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` / `STORAGE_BUCKET` / `STORAGE_REGION` | S3-compatible object storage | Books/3D/media uploads (signed URLs) |
| `REDIS_URL` | Managed Redis (optional) | Rate-limit / cache / queues; falls back to in-memory if unset |
| LLM API key (e.g. `OPENAI_API_KEY`) | Step 13 AI (optional) | Only if swapping the deterministic answer builder for a hosted model |
| `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SITE_URL` | Vercel frontend | Point the web app at the hosted API/auth |
| Vercel token / Render (or Railway) token | Deployment | Auto-deploy on push |

**For the next (deployment) batch I'll need:** Supabase project URL + JWT secret + service-role key, a managed Postgres `DATABASE_URL`, S3-compatible credentials (endpoint/key/secret) or an alternative, and a Vercel (or Render/Railway) account/token. I can build the signed-URL upload + pgvector integration without them (using a local-storage mock + SQLite), and wire the real providers the moment you provide the values.

---

*Generated by the MEDFREE build agent. End of Steps 16–20 combined audit.*
