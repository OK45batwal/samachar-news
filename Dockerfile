# ── Stage 1: Frontend build ──
FROM node:22-alpine AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend/ frontend/
COPY vite.config.js postcss.config.js ./
RUN npm run build

# ── Stage 2: Python runtime ──
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev python3-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY --from=frontend /build/frontend/dist frontend/dist
COPY alembic/ alembic/
COPY alembic.ini .
COPY .env.example .

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}
