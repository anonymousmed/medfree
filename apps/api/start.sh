#!/bin/sh
# MEDFREE API production boot: apply migrations, (optionally) seed, serve.
set -e

export PYTHONPATH=/app

echo "[boot] Applying database migrations (alembic upgrade head)..."
alembic upgrade head

if [ "${SEED_ON_BOOT:-true}" = "true" ]; then
  echo "[boot] Seeding database..."
  python -m scripts.seed_dev
fi

echo "[boot] Starting uvicorn on 0.0.0.0:${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
