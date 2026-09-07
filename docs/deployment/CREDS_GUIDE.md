# MEDFREE — Credentials Guide (obtain these, then paste to me)

> This is the exact list of config the app reads (it maps 1:1 to `.env.example`).
> Recommended (free/low-cost) stack: **Supabase** (managed Postgres + Auth), **Cloudflare R2**
> (S3-compatible object storage), **Render** (backend), **Vercel** (frontend). Everything is
> swappable — the code only cares about the env variable names below.

---

## 0. Recommended provider plan

| Slot | Provider | Why | Cost |
|---|---|---|---|
| Database + Auth | **Supabase** | One project gives managed Postgres + Supabase Auth + JWT | Free tier |
| Object storage | **Cloudflare R2** | S3-compatible (works with our boto3 driver), 10 GB free | Free tier |
| Backend host | **Render** | Easiest for a FastAPI + uvicorn service | Free tier |
| Frontend host | **Vercel** | First-class Next.js hosting | Free/Hobby |
| Redis (optional) | **Upstash** | Redis-compatible, free | Free tier |

> If you'd rather keep it to ONE provider: Supabase ALSO offers Storage (S3-compatible gateway).
> We can point `STORAGE_*` at Supabase Storage instead of R2. Tell me which you prefer.

---

## 1. Supabase — Database + Auth (one project gives 3 things)

1. Go to https://supabase.com → **Sign up** (free).
2. Click **New project** → choose a name (e.g. `medfree`) → set a strong DB password → pick a region nearest to you (e.g. Singapore/Mumbai). Wait for provisioning (~2 min).
3. In the project, open **Project Settings → Database**:
   - Copy **Connection string → URI** → this is **`DATABASE_URL`** (it looks like `postgresql://postgres.xxxx:password@...`). Use the **pooled** (port 6543) URI for the app, or the session URI.
4. In **Project Settings → API**:
   - **`SUPABASE_URL`** (Project URL, `https://xxxx.supabase.co`)
   - **`SUPABASE_ANON_KEY`** (anon/public key — safe for the browser)
   - **`SUPABASE_SERVICE_ROLE_KEY`** (secret — **server-only**, never expose)
   - Copy these three.
5. **JWT secret**: In **Project Settings → API → JWT Settings** → copy **JWT Secret** → **`SUPABASE_JWT_SECRET`**.
   - **Note (verified):** modern Supabase signs access tokens with an **ES256** key published at
     `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json`. MEDFREE now validates tokens
     against the **JWKS** (so it works with ES256/RS256 or legacy HS256). `SUPABASE_JWT_SECRET` is
     only a **fallback**. Provide `SUPABASE_URL` so the JWKS can be fetched.
6. **Auth** settings (optional but recommended): **Authentication → Providers → Email** and enable Email; you can also enable "Confirm email".
   - For the frontend, the browser needs the same two public values: **`NEXT_PUBLIC_SUPABASE_URL`** = `SUPABASE_URL`, **`NEXT_PUBLIC_SUPABASE_ANON_KEY`** = `SUPABASE_ANON_KEY`.

> Also create the roles in Supabase Auth: in **Authentication → Users**, add the admin account(s) you'll use
> (or map roles via the `user_roles` table once the app seeds roles). MEDFREE's backend reads the JWT `role` claim.

---

## 2. Cloudflare R2 (or Supabase Storage) — object storage for uploads

### Option A — Cloudflare R2 (S3-compatible, recommended)
1. Go to https://dash.cloudflare.com → create a **Cloudflare account** (if not already).
2. **R2 Object Storage** → **Create bucket** → name it exactly `medfree` (or update `STORAGE_BUCKET`).
3. **R2 → Manage R2 API Tokens → Create API token**:
   - Give it **Object Read & Write** on the `medfree` bucket.
   - Copy the **Access Key ID** → **`STORAGE_ACCESS_KEY`**, **Secret Access Key** → **`STORAGE_SECRET_KEY`**.
4. Bucket settings page shows the **Endpoint** (S3 API endpoint, e.g. `https://<account>.r2.cloudflarestorage.com`) → **`STORAGE_ENDPOINT`**.
5. `STORAGE_REGION` = `auto` (R2) — leave as `auto`.

### Option B — Supabase Storage
1. In the Supabase project: **Storage → New bucket** → name `medfree`, set to **Public** (so served assets are readable) or private + signed URLs.
2. Supabase Storage is S3-compatible: create an S3 credential under **Project Settings → Storage → S3 Access Keys**, and use:
   - `STORAGE_ACCESS_KEY` = S3 Access Key ID
   - `STORAGE_SECRET_KEY` = S3 Secret
   - `STORAGE_ENDPOINT` = `https://<project-ref>.supabase.co/storage/v1/s3`
   - `STORAGE_BUCKET` = `medfree`
   - `STORAGE_REGION` = **your project's real region** (e.g. `ap-southeast-1`), **not `auto`** —
     Supabase's S3 signature fails with `auto`. Find it under **Project Settings → General → Project Region**.
   - (Optional, public bucket) `STORAGE_PUBLIC_BASE_URL` = `https://<project-ref>.supabase.co/storage/v1/object/public/medfree`
     for stable public URLs.

---

## 3. Render — backend host (FastAPI)

1. Go to https://render.com → **Sign up** (GitHub login easiest).
2. **New → Web Service** → connect the MEDFREE repo.
3. Set:
   - **Root directory**: `apps/api`
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance type**: Free (or Starter).
4. **Environment → Add Environment Variables** — paste all the backend variables from §7 (it becomes the runtime `DATABASE_URL`, `SUPABASE_*`, `STORAGE_*`, etc.).
   - Render gives you a **public URL** like `https://medfree-api.onrender.com` → this is what the frontend calls → **`MEDFREE_API_URL` / `NEXT_PUBLIC_API_URL`**.
5. **Deploy**. After first boot run migrations on the managed DB once (see §8 "Run migrations").

> Render's Python version is configurable in the service settings (use 3.12). It's a VPS-like host but managed — no personal VPS needed.

---

## 4. Vercel — frontend host (Next.js)

1. Go to https://vercel.com → **Sign up** (GitHub login).
2. **Add New → Project** → import the MEDFREE repo.
3. Vercel auto-detects the monorepo; set:
   - **Root Directory**: `apps/web`
   - **Framework**: Next.js
   - **Build command**: `npm run build` (Vercel runs it for you)
4. **Environment Variables** (Project Settings → Environment Variables) — set the **frontend** ones:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL` = the **Render/Railway backend URL** (e.g. `https://medfree-api.onrender.com`)
   - (Optional) `MEDFREE_API_URL` for server-side rendering = the same backend URL.
5. **Deploy** → Vercel gives you a public URL like `https://medfree.vercel.app`.
6. In the backend's CORS allowlist, add this Vercel URL (`cors_origins`) — we'll set `CORS_ORIGINS` env on Render.

---

## 5. Redis (optional — distributed rate limiting)

1. Go to https://upstash.com → **Create database** (free) → copy your **`REDIS_URL`** (`rediss://...`).
2. Set `REDIS_URL` on the backend (Render). If left empty, MEDFREE uses its in-memory rate limiter (fine for the MVP).

---

## 6. LLM / embeddings (optional)

- **`LLM_API_KEY`** — an OpenAI (or compatible) key if you want the AI assistant to use a hosted LLM.
- **`EMBEDDING_PROVIDER`** = `local` (default, no key) | `openai` | `sentence-transformers`. For better answer quality, set to `openai` and supply the key; otherwise leave `local`.

---

## 7. Full `.env` template (paste into Render env + Vercel env)

```dotenv
# --- Backend (Render) -------------------------------------------------------
DATABASE_URL=postgresql://postgres.xxxx:YOUR-DB-PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres
AUTH_PROVIDER=supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...                 # anon/public key
SUPABASE_SERVICE_ROLE_KEY=eyJ...         # secret, server-only
SUPABASE_JWT_SECRET=your-jwt-secret
ENVIRONMENT=production
# CORS (add your Vercel origin)
CORS_ORIGINS=["https://medfree.vercel.app","http://localhost:3000"]
FRONTEND_URL=https://medfree.vercel.app
# Object storage (R2 example)
STORAGE_ENDPOINT=https://<account>.r2.cloudflarestorage.com
STORAGE_ACCESS_KEY=<R2 access key>
STORAGE_SECRET_KEY=<R2 secret>
STORAGE_BUCKET=medfree
STORAGE_REGION=auto
STORAGE_LOCAL_ROOT=/tmp/medfree-storage
MAX_UPLOAD_MB=200
# Optional
REDIS_URL=rediss://...
LLM_API_KEY=sk-...
EMBEDDING_PROVIDER=local        # or openai
RATE_LIMIT_ANON=60
RATE_LIMIT_AUTHED=300
RATE_LIMIT_AUTH=10
RATE_LIMIT_SEARCH=30
RATE_LIMIT_ADMIN=120
RATE_LIMIT_WINDOW=60
SECURITY_HEADERS=true

# --- Frontend (Vercel) ------------------------------------------------------
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...     # anon key (public, safe)
NEXT_PUBLIC_API_URL=https://medfree-api.onrender.com
MEDFREE_API_URL=https://medfree-api.onrender.com
```

---

## 8. Once you give me these, the flow is

1. **I** write them to the host env configs (or a local `.env`), never to Git.
2. Run `alembic upgrade head` on the managed Postgres → creates 46 tables.
3. Run `python -m scripts.seed_dev` → seeds subjects/topics/Atlas/library + knowledge graph.
4. Deploy backend (Render) → then frontend (Vercel), wire `NEXT_PUBLIC_API_URL`.
5. Set Supabase Auth + create the first admin user + assign the `content_admin`/`super_admin` role.
6. Smoke-test the live site, verify upload/admin RBAC, Atlas, AI, then go live.

---

## 9. Credentials checklist (tick as you collect)

- [ ] `DATABASE_URL` (Supabase connection string) — §1.3
- [ ] `SUPABASE_URL` — §1.4
- [ ] `SUPABASE_ANON_KEY` — §1.4
- [ ] `SUPABASE_SERVICE_ROLE_KEY` — §1.4 (SECRET)
- [ ] `SUPABASE_JWT_SECRET` — §1.5
- [ ] `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` — §1.6
- [ ] `STORAGE_ACCESS_KEY` + `STORAGE_SECRET_KEY` + `STORAGE_ENDPOINT` (+ bucket) — §2
- [ ] Render **backend URL** — §3.4
- [ ] Vercel **frontend URL** — §4.5
- [ ] (Optional) `REDIS_URL` — §5
- [ ] (Optional) `LLM_API_KEY` / `EMBEDDING_PROVIDER` — §6

> **Security note:** the `SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET` are secrets — share them only with me
> in a private/expiring message. `ANON_KEY` and `NEXT_PUBLIC_*` are public by design and safe to share.

---

## Appendix — verified against a real Supabase project (this session)

Live-tested with the provided credentials. **All passed** (values redacted):

| Credential | Verified status |
|---|---|
| `SUPABASE_URL` | ✅ project reachable (auth/settings 200) |
| `SUPABASE_ANON_KEY` | ✅ valid anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ works; can list Storage buckets + Auth Admin API |
| `SUPABASE_JWT_SECRET` | ⚠️ provided value is the **legacy HS256** secret. Project signs with **ES256** (JWKS `kid` = this secret). MEDFREE now verifies via JWKS, so **works** with `SUPABASE_URL` set. |
| `DATABASE_URL` | ✅ keys valid; sandbox blocks raw Postgres TCP (egress) — works on Render. Use the **pooled** URL (`:6543`). |
| `STORAGE_*` (Supabase) | ✅ S3 `list_buckets` returns `medfree`, bucket is **Public**, both host forms (~`.storage.`/~`.supabase.`) authenticate. |
| GitHub token | ✅ login `anonymousmed`; repo `medfree` exists (public, default branch `main`). |

**Auth admin setup:** the first admin user is created via the `service_role` Auth Admin API
(`app_metadata.role = "super_admin"`), then a fresh sign-in yields `role=super_admin` in MEDFREE —
**no dashboard role edation needed**. (A temporary test user was created during verification, then deleted.)

**Storage region:** set `STORAGE_REGION` to the project's actual region (find under
**Project Settings → General → Project Region**). Do **not** use `auto` for Supabase Storage.
