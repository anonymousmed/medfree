# MEDFREE

> **A free, tablet/desktop-first digital medical university with full phone compatibility.**
> Its core experience is interactive medical learning centered around the **Human Atlas**, visual explanations, practical learning, clinical cases, MCQs, viva, flashcards, and personalized study. Books and research resources provide the underlying knowledge and references.

**Learn → Explore → Practice → Master**

---

## Multi-paradigm summary

| Layer | What it is |
|---|---|
| **Primary** | Human Atlas + Interactive Learning |
| **Secondary** | Structured Medical Education (diagrams, animations, clinical, MCQs, viva, flashcards) |
| **Knowledge Foundation** | Books + Research + Trusted References |
| **Intelligence Layer** | AI + Personalized Learning + Recommendations |
| **Platform Layer** | Accounts + Progress + Admin + Analytics + Security |

**Core mandates (non-negotiable):**
1. Tablet/Desktop-first, full phone compatibility.
2. Human Atlas is the centerpiece; books are the reference layer.
3. Only authorized admins/content admins can directly upload books & official resources — **enforced at the backend** (students/contributors receive `403`).
4. **No personal VPS required** — deploy on managed services (Vercel + Render/Railway + managed PostgreSQL + managed object storage).

---

## Repository layout

```
medfree/
├── apps/
│   ├── web/            Next.js + TypeScript + Tailwind (Vercel)
│   └── api/            FastAPI + SQLAlchemy + Alembic (Render/Railway)
├── packages/
│   ├── types/          Shared TS types (@medfree/types)
│   ├── config/         App constants + Tailwind preset (@medfree/config)
│   ├── ui/             Design system components (@medfree/ui)
│   └── atlas/          3D Atlas viewer (R3F + drei, @medfree/atlas)
├── database/
│   ├── schema/         Reference SQL schema
│   ├── migrations/     Alembic migrations (symlinked into apps/api)
│   └── seeds/          Seed datasets
├── docs/               architecture, api, deployment, atlas, content, licensing
├── docker/             container config
├── scripts/            helper scripts
├── tests/              pytest suite (backend)
├── .github/            CI workflows
├── docker-compose.yml  OPTIONAL local full-stack parity
└── .env.example
```

> Note: the backend's Alembic migration folder lives at `apps/api/migrations` (the canonical location for the API service). `database/migrations` references it; keep them in sync when autogenerating.

---

## Quick start (local)

### 1. Backend (FastAPI)

```bash
cd apps/api
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # AUTH_PROVIDER=mock, AUTH_BYPASS=true by default
python -m scripts.seed_dev        # creates a local sqlite DB with starter content
uvicorn app.main:app --reload     # http://localhost:8000  (/docs for OpenAPI)
```

### 2. Frontend (Next.js)

```bash
# from repository root
npm install --legacy-peer-deps
npm run dev:web                   # http://localhost:3000
```

The web app proxies `/api/*` to the backend (see `apps/web/next.config.mjs`). If it can't reach the API it falls back to bundled mock data, so the UI always renders.

### 3. Tests

```bash
cd apps/api && . .venv/bin/activate
python -m pytest ../../tests -q
```

The RBAC suite verifies **students/contributors get `403`** on upload and that admins can publish only verified content.

---

## Cloud deployment (no VPS)

Target architecture:

```
Student Device
   ↓  Cloudflare / CDN
Vercel — Next.js Frontend
   ↓
Render / Railway — FastAPI Backend (+ background workers)
   ↓
Managed PostgreSQL   (Supabase / Railway / Render)
   ↓
Object Storage       (S3-compatible)
   ↓
Redis / Workers      (as required)
```

- **Frontend:** Vercel → build `apps/web`, set `NEXT_PUBLIC_API_URL` to the hosted backend URL.
- **Backend:** Render/Railway → root `apps/api`, command `uvicorn app.main:app --host 0.0.0.0 --port 8000`, run migrations (`alembic upgrade head`) at deploy.
- **DB:** managed PostgreSQL → set `DATABASE_URL`.
- **Auth:** Supabase → set `AUTH_PROVIDER=supabase`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY`.

See [docs/deployment/CLOUD.md](docs/deployment/CLOUD.md) for provider-specific step-by-step.

---

## Documentation

- [Architecture](docs/architecture/OVERVIEW.md)
- [Cloud deployment](docs/deployment/CLOUD.md)
- [API specification](docs/api/OPENAPI.md) · live at `/docs`
- [ER diagram + schema](database/schema/schema.sql)
- [Human Atlas architecture](docs/atlas/FOUNDATION.md) & [3D asset pipeline](docs/atlas/3D_PIPELINE.md)
- [Rights / licensing model](docs/licensing/RIGHTS_MODEL.md)
- [Content sourcing](docs/content/SOURCES.md)

Master build specification: [`MEDFREE_FINAL_AGENT_MASTER_BUILD_SPEC_UPDATED.md`](../MEDFREE_FINAL_AGENT_MASTER_BUILD_SPEC_UPDATED.md) (at repo root).

---

## License

Source code: MIT (see [LICENSE](LICENSE)). **Educational content is governed by each resource's own license/rights record** — see [docs/licensing/RIGHTS_MODEL.md](docs/licensing/RIGHTS_MODEL.md). Never assume imported content is reusable just because it's viewable online.
