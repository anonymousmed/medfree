"""Provider-agnostic embeddings for RAG retrieval (spec §27).

Two paths, same interface:
- ``embed()`` returns a dense vector (list[float]).
- In production you can swap ``embed()`` to call a hosted embedding model
  (OpenAI, Voyage, Cohere, or a local SentenceTransformer) behind the same
  signature. In local/CI (and as a deterministic default) we compute a
  hashed bag-of-tokens vector so retrieval works without any API key, and a
  real model can be dropped in by setting ``settings.embedding_provider``.

Vector similarity is computed as cosine similarity over the vectors. With
PostgreSQL + pgvector, the vectors are stored natively and similarity can be
computed in SQL; here we use the portable JSON rep + in-memory cosine.
"""
from __future__ import annotations

import hashlib
import json
import math
import re


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-']*", text.lower())


def _hash_token(token: str, dim: int, seed: int) -> int:
    h = hashlib.blake2b(token.encode(), digest_size=8, key=seed.to_bytes(4, "little")).hexdigest()
    return int(h, 16)


def embed(text: str, dim: int = 256) -> list[float]:
    """Deterministic hashed embedding (works offline / on SQLite).

    Swappable for a hosted model by returning its vector instead.
    """
    vec = [0.0] * dim
    tokens = _tokens(text)
    if not tokens:
        return vec
    for t in tokens:
        # Sign by token hash parity so the vector isn't all-positive.
        idx = _hash_token(t, dim, 1) % dim
        sign = 1.0 if (_hash_token(t, dim, 2) % 2 == 0) else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def encode_vector(vec: list[float]) -> str:
    return json.dumps(vec)


def decode_vector(raw: str | None) -> list[float]:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []
