# MEDFREE — Rights & Licensing Model

> **"Available online for free" does NOT mean "free to copy, rehost, modify or sell."**

## Core rule

The platform's MIT license applies to **MEDFREE's own source code only**. Every piece of content (books, PDFs, EPUBs, images, diagrams, 3D models, MCQs, etc.) carries its own **rights record** and is governed by that record — not by the source-code license.

## Rights statuses (`resources.rights_status`)

| Status | Meaning |
|---|---|
| `verified` | Rights confirmed |
| `permission_granted` | Explicit permission obtained |
| `public_domain` | Public domain |
| `open_license` | Openly licensed (CC, etc.) |
| `external_only` | Link/embed only; no local copy |
| `review_required` | **Do not publish** |
| `blocked` | Do not use |

## License fields (`licenses`)

`name`, `license_url`, `commercial_allowed`, `modification_allowed`, `redistribution_allowed`, `attribution_required`, `sharealike_required`, **`ai_ingestion_allowed`**, `notes`.

## AI ingestion

Each resource has `ai_usage_status`: `true` / `false` / `unknown`. **`unknown` = DO NOT INGEST** into the AI/RAG layer. This is essential because some licenses restrict AI use.

## Booking / hosting decisions per resource

- **Openly licensed & compatible** → use according to the license (show attribution, obey SA/NC).
- **Public domain** → use per applicable law.
- **Permission granted** → use per permission.
- **External-only** → link/embed legitimately; **no local copy**.
- **Uncertain** → do **not** copy/rehost until reviewed. Set `review_required`.

## Example
OpenStax textbooks are **CC BY-NC-SA** (verify per title; a few titles are CC BY): share/adapt noncommercially with attribution + ShareAlike; commercial reuse requires permission. Do not assume all "free books" share the same permissions.

## AI ingestion — important caveat
A CC licence that permits sharing/adapting does **not** automatically permit ingesting the text into an LLM / AI-RAG system. OpenStax's own preface for newest editions states the book **"may not be used in the training of large language models or otherwise be ingested into large language models or generative AI offerings without OpenStax's permission."** MEDFREE therefore records OpenStax titles with `ai_usage_status='false'` regardless of the CC licence. The curated library (`scripts/library_pack.py`) follows this rule for every resource: AI ingestion is `true` only for genuinely public-domain / explicitly-permitted material; everything uncertain is `unknown` (which the ingestion policy treats as *do not ingest*).

## Publish gate
Even **admins** cannot publish a resource whose `rights_status = review_required` (verified by tests).
