# MEDFREE — API Specification

Live OpenAPI docs: `GET /docs` (FastAPI) — non-production.

Base URL (dev): `http://localhost:8000/api`
Auth: `Authorization: Bearer <access_token>` (Supabase JWT) — or mock token in dev.

> **RBAC by default.** The backend returns `403` for unauthorized roles regardless of frontend UI.

## Roles ladder
`student (0) < contributor (1) < reviewer (2) < medical_reviewer (3) < moderator (4) < content_admin (5) < super_admin (6)`

---

## Auth (`/auth`)
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/auth/me` | user | Current profile (local user row + highest role) |
| GET | `/auth/identity` | user | Decoded token identity (sub, email, role) |

Register/login/reset are handled by Supabase Auth on the frontend.

## Subjects (`/subjects`)
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/subjects` | public | List subjects |
| GET | `/subjects/{slug}` | public | Subject detail |
| GET | `/subjects/{slug}/topics` | public | Topics for a subject |
| GET | `/subjects/{subject}/topics/{topic}` | public | Topic detail |

## Atlas (`/atlas`) — centerpiece
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/atlas/regions` | public | List regions |
| GET | `/atlas/regions/{slug}` | public | Verified structures in a region |
| GET | `/atlas/structures` | public | List/filter structures (region, system) |
| GET | `/atlas/structures/{slug}` | public | Structure detail |
| GET | `/atlas/models/{id}` | public | Published 3D model metadata |
| GET | `/atlas/search?q=` | public | Structure search |

## Resources (`/resources`) — RBAC-critical
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/resources` | public | Published, public resources |
| GET | `/resources/{id}` | public | Resource detail |
| POST | `/resources/upload` | **content_admin/super_admin** | Admin upload (students/contributors → **403**) |
| POST | `/resources/submit` | authenticated (contributor) | Submit → enters review; never auto-publishes |
| PATCH | `/admin/resources/{id}` | admin | Edit resource |
| DELETE | `/admin/resources/{id}` | admin | Archive/delete |

## Admin (`/admin`) — all routes require admin
| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/stats` | Counts (users, resources) |
| GET | `/admin/resources` | All resources incl. unverified |
| POST | `/admin/resources/{id}/publish` | Publish (blocked if `rights_status=review_required`) |

## Example RBAC behaviors (tested)
```
POST /api/resources/upload  (student)      → 403
POST /api/resources/upload  (contributor)  → 403
POST /api/resources/submit  (contributor)  → 201 (review_status=draft)
POST /api/resources/upload  (content_admin)→ 201
POST /api/resources/upload  (super_admin)  → 201
POST /api/resources/upload  rights_status=review_required → 422 (even for admin)
```
See `tests/test_rbac_upload.py`.
