# MEDFREE — Managed Cloud Deployment (no VPS)

> **The user's personal VPS is NOT required.** Deploy using managed services.

## Target architecture

```
Student Device (Laptop/Desktop/Tablet/Phone)
        ▼
Cloudflare / CDN  (free tier where appropriate)
        ▼
Vercel — Next.js Frontend (apps/web)
        ▼
Render / Railway — FastAPI Backend (apps/api) + background workers
        ▼
Managed PostgreSQL          (Supabase / Railway / Render — pick one)
        ▼
S3-compatible Object Storage (books, PDFs, EPUBs, images, 3D, video)
        ▼
Redis / Background Workers    (as required)
```

Portability rule: each external service is referenced through a thin abstraction and env var, so any provider can be swapped later.

---

## Frontend → Vercel

1. Import the repo; **Root Directory** = `apps/web` (or set to repo root with build at `apps/web`).
2. Build command: `npm install --legacy-peer-deps && npm run build` (or rely on Vercel's monorepo awareness).
3. Output directory: `.next` (default).
4. Set env vars:
   - `NEXT_PUBLIC_SITE_URL` = your domain
   - `NEXT_PUBLIC_API_URL` = your hosted backend URL, e.g. `https://medfree-api.onrender.com`
   - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. Deploy → auto deploy on Git push.

---

## Backend → Render (or Railway)

**Render service (Web Service):**
- Root Directory: `apps/api`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Env:
  - `AUTH_PROVIDER=supabase`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`
  - `DATABASE_URL` = `postgresql+asyncpg://…` (managed Postgres)
  - `CORS_ORIGINS` = `["https://your-app.vercel.app"]`
- **Migrations:** set the Pre-Deploy command to `alembic upgrade head`.

**Background worker (optional later):** add a Render Background Worker / Railway job service for content ingestion, model optimization, email, etc.

**Railway alternative:** same start command; Railway can provision Postgres + Redis as plugins; set `DATABASE_URL` and optionally `REDIS_URL`.

---

## Database

Pick one managed PostgreSQL provider; the app only reads `DATABASE_URL`:
- Supabase (advisory: shares the auth project, convenient)
- Railway PostgreSQL
- Render PostgreSQL
- Any other compatible provider

Enable backups. Keep `DATABASE_URL` in secrets.

---

## Object storage

Use any S3-compatible store (Cloudflare R2 free tier, Supabase Storage, AWS S3, Backblaze B2). The abstraction reads `STORAGE_*` env vars. Medium/large files (books, 3D assets, videos) go here, not the DB or app FS.

---

## Auth

- `AUTH_PROVIDER=supabase` enables Supabase JWT verification in the backend (`app/core/auth.py`).
- Set `supabase_jwt_secret` so the backend can verify access tokens.
- Roles are mapped from `app_metadata.role` (student/contributor/reviewer/medical_reviewer/moderator/content_admin/super_admin).

---

## CI/CD

`.github/workflows/ci.yml` runs backend lint+tests and a web build on every PR. Add a production gate that runs `alembic upgrade head` before deploy and the RBAC/upload smoke tests.

---

## Cost posture

- **MVP:** free tiers (Vercel Hobby, Render free, Supabase free, R2 free, Cloudflare free) — realistic for low traffic.
- **Growing platform:** budget for storage, bandwidth, DB, compute, backups, AI APIs, email, domain, CDN, professional medical review, licensed content, large 3D assets, high traffic. Do **not** claim the whole production platform stays free forever.
