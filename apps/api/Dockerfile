# MEDFREE API — FastAPI (Builds on Render/Railway or locally).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*

# Install runtime deps (a slim, correct subset for the image).
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the app, migrations and seeding scripts.
COPY apps/api/app ./app
COPY apps/api/migrations ./migrations
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/scripts ./scripts
COPY apps/api/start.sh ./start.sh
RUN chmod +x /app/start.sh

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["/app/start.sh"]
