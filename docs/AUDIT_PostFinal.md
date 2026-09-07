# MEDFREE — Post-Final Verification & Content-Expansion Audit

> Follow-up task: independently re-verify the codebase (not the prior audit), fix real
> issues, add a rights-aware initial book library, add the curriculum knowledge graph,
> harden security, and prepare for managed-cloud deployment. No deployment performed;
> credentials are requested in the next phase.

---

## 1. Audit result

**Passed (with fixes).** The prior audit ("final") was largely accurate, but independent
inspection found and fixed the following real issues (none were hidden or worked around):

| # | Issue found | Severity | Fix |
|---|---|---|---|
| 1 | **Fabricated resource**: "Open Anatomy Reference" with `source_url=https://example.com/` was seeded. | Blocking (fake URL) | Removed from `seed_dev.py`; replaced by a rights-aware library with real, verified sources. |
| 2 | **Wrong license/AI flag**: seeded "Anatomy & Physiology" was labeled **CC BY 4.0** and `ai_usage_status='true'`. OpenStax A&P 2e is actually **CC BY-NC-SA 4.0** and **prohibits AI ingestion**. | Rights | Corrected to CC BY-NC-SA + `ai_usage_status='false'`; added the A&P licence. |
| 3 | **False "medically approved"**: seeds set `medical_review_status='approved'` for books we never medically reviewed. | Medical-integity | All curated books now `pending_medical_review` (honest). |
| 4 | **No knowledge graph**: Topic model had no prerequisite/related/next/difficulty. | Feature gap | Added `TopicLink` + `difficulty`/`est_minutes`; built + seeded a 16-edge graph; exposed via API + UI. |
| 5 | **No upload size limit**; `serve_storage` exposed any stored key (not gated to public). | Security | Added `max_upload_mb` (default 200) enforced at API + local driver; serve only public/published resources (404 otherwise). |
| 6 | **(Venv/node_modules not persisted)** — sandbox reset; re-installed. | Environment | Re-provisioned; all tests/build verified on fresh deps. |

---

## 2. Test results (fresh, post-fix)

- **Backend `pytest`** → **61 passed** (55 prior + 2 knowledge-graph/library + 4 security-hardening). `tests/test_knowledge_graph_library.py`, `tests/test_security_hardening.py`.
- **Frontend `tsc --noEmit`** → **0 errors**.
- **Next.js production build** → **20 routes**, success.
- **Migrations on a clean DB** → `alembic upgrade head` works from zero → **46 tables** (added `topic_links`).
- **Seed idempotency** → re-running `seed_dev` twice yields identical counts (no duplicates).
- **API smoke (live)** → health, RBAC, topic knowledge graph, size limit (413/200), serve gate, AI ask — all green.

---

## 3. Content (post-verification)

- **Subjects**: 3 (Anatomy, Physiology, Biochemistry)
- **Topics**: 14 (curated)
- **Topic blocks (learning flow)**: 154
- **Questions (MCQs)**: 14, **Viva**: 11, **Flashcards**: 15, **Practicals**: 5
- **Books/resources**: 11 in curated library + 9 book rows + 17 chapters
- **Atlas**: 29 structures, 7 regions, 7 systems, 1 model + 3 parts, 3 annotations
- **Knowledge graph**: 16 edges (prerequisite / related / next)
- **Licenses**: 7 accurately-flagged licence records

## 4. Book library (new) — see `scripts/library_pack.py`

| Title | Subject | Author/publisher | Source | Licence | Rights | Host | AI |
|---|---|---|---|---|---|---|---|
| Anatomy & Physiology 2e | Anatomy | OpenStax (Betts et al.) | openstax.org/books/anatomy-and-physiology-2e | CC BY-NC-SA 4.0 | open_license | host/embed | `false` |
| Anatomy & Physiology 2e (Oregon State) | Anatomy | Biga et al., OSU | open.oregonstate.education/anatomy2e | CC BY-SA 4.0 | open_license | host | `unknown` |
| Gray's Anatomy (1918) | Anatomy | Henry Gray | (Wikipedia) | Public Domain (US) | public_domain | external | `true` |
| BodyParts3D / Anatomography | Anatomy | BodyParts3D | github (Moerman) | CC BY-SA 2.1 JP | open_license | host | `false` |
| Biology 2e | Physiology | Clark, Douglas, Choi (OpenStax) | openstax.org/books/biology-2e | CC BY-NC-SA 4.0 | open_license | host/embed | `false` |
| Human Physiology (NCBI ref) | Physiology | NCBI Bookshelf | ncbi.nlm.nih.gov/books | Publisher retained | external_only | **external** | `false` |
| Biochemistry, 5th ed. | Biochemistry | Berg, Tymoczko & Stryer (W.H. Freeman) | ncbi.nlm.nih.gov/books/NBK21154 | Publisher retained | external_only | **external** | `false` |
| Molecular Biology of the Cell, 4th ed. | Biochemistry | Alberts et al. (Garland) | ncbi.nlm.nih.gov/books/NBK21054 | Publisher retained | external_only | **external** | `false` |
| Biochemistry: Free For All | Biochemistry | Ahern, Rajagopal, Tan (OSU) | open.umn.edu | CC BY-NC 4.0 | open_license | host | `false` |
| Fundamentals of Biochemistry | Biochemistry | Jakubowski & Flatt | bio.libretexts.org | CC BY-NC-SA 4.0 | external_only | **external** | `unknown` |
| Heart Diagram (cross-section) | Physiology | DrJanaOfficial | Wikimedia Commons | CC BY-SA 4.0 | open_license | host | `false` |

> External-only rows are **never downloaded/rehosted** — they link to the legitimate source
> (NCBI Bookshelf, LibreTexts) only. Openly-licensed rows may be hosted per licence with
> attribution (+ ShareAlike). No resource is AI-ingested unless explicitly permitted.

## 5. Atlas

- **Current capability**: working viewer foundation + structure/region/system/label/annotation
  data + relations. Serving 29 structures, 7 regions, 7 systems.
- **Asset count**: 1 atlas model, 3 model parts, 3 annotations — this is a **seed skeleton**,
  **not** thousands of real 3D meshes.
- **Licensing/attribution**: BodyParts3D record (CC BY-SA 2.1 JP) added to the library for
  legitimate asset use.
- **NOT VERIFIED / not integrated**: full real-mesh integration (e.g., ashemag/human-atlas
  or BodyParts3D meshes loaded into the viewer), cross-sections, clinical-mode 3D, quiz-in-3D.
  These are roadmap items requiring the 3D asset pipeline + licensing confirmation, and are
  out of scope for this pass.

## 6. Security

- **RBAC**: admin-only upload/AI-index (Student/Contributor/Reviewer → 403) — verified by test + live.
- **Upload protection**: extension allowlist by resource type; **size limit** (200 MB) added;
  path-traversal guard in storage driver; UUID storage keys.
- **Serve gate**: storage serve returns 404 unless the resource is public/published.
- **Rate limiting** + **audit logs** + **security headers** — present (verified earlier).
- **Secrets**: no hardcoded secrets in source; `.gitignore` excludes `.env*` (except `.env.example`).

## 7. Deployment readiness

- **Ready**: .env.example complete (incl. `MAX_UPLOAD_MB`, `STORAGE_*`, `SUPABASE_*`, `DATABASE_URL`,
  `REDIS_URL`, `LLM_API_KEY`, `EMBEDDING_PROVIDER`, rate limits, security headers); provider-agnostic
  storage + embedding drivers; migrations on clean DB; idempotent seed; Dockerfiles + docker-compose
  + CI; configurable CORS + frontend/API base URLs.
- **Still requires credentials** (next phase): `DATABASE_URL`, Supabase keys, `STORAGE_*`, optional
  `REDIS_URL`, and Vercel/Render/Railway tokens. Nothing was deployed.

## 8. Remaining issues (genuine only)

- **Important — no content served for `NEXT_PUBLIC_API_URL` mismatch in prod**: set it to the hosted backend
  (documented). Not a code bug.
- **Important — recommend real embeddings/LLM key** for better AI answer quality (current deterministic
  hashed embeddings are an intentional MVP).
- **Optional — stricter `serve_storage` for S3**: presigned URLs currently grant the key; verify public
  buckets/objects are read-only and don't accidentally allow overwrite.
- **Optional — phone performance on low/mid Android** and real-mesh Atlas: **NOT VERIFIED** (no device/testing here).
- **Optional — medical review gate** before any clinical claim is authoritative (seed is reference material).
