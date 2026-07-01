# Samachar News — Project Roadmap

A full-stack news intelligence platform: FastAPI + vanilla HTML/CSS/JS, SQLite/PostgreSQL, RSS ingestion, AI insights.

---

## Phase 1: Polish & Bugfixes (Current)
Objective: Fix all known UI/UX issues and stabilize the app.

- [x] SECRET_KEY persistence across restarts
- [x] DB-backed rate limiting (was in-memory)
- [x] Cache-busting on all static assets
- [x] Theme toggle on all pages (was only index)
- [x] Missing sidebars/search overlays on inner pages
- [x] Hardcoded colors → CSS variables
- [x] Responsive grid layouts for mobile
- [x] Admin duplicate cards bug
- [x] Article page bookmark ID hardcoded
- [x] Removed Live TV page (legal)
- [x] Fix category tab active state on Latest page (data-cat, URL sync)
- [x] Add loading states for all async operations
- [x] Handle API errors gracefully (error messages, not silent catch)

## Phase 2: Containerization & Database
Objective: Portable, production-ready infrastructure.

- [x] Add Dockerfile (Python 3.14 slim)
- [x] Add docker-compose.yml (app + PostgreSQL + Redis)
- [x] Switch default DB to PostgreSQL in Docker
- [x] Add Alembic migrations (replace auto-create tables)
- [x] Add `gunicorn` to requirements
- [x] Add health check endpoint (`GET /api/health`) with DB check
- [x] Tune DB connection pooling for production
- [x] Create `.env.example` with all config keys documented
- [x] Update `.gitignore` for `data/` and Docker files

## Phase 3: Background Jobs
Objective: Move feed ingestion out of the request-response cycle.

- [x] Lightweight task manager (no Celery/Redis required)
- [x] Move RSS ingestion to background worker with DB status tracking
- [x] Scheduled auto-ingestion every 30 min via asyncio loop
- [x] `IngestionRun` model — tracks status, counts, errors per run
- [x] Admin ingest returns `run_id`, frontend polls status endpoint
- [x] Per-feed isolated DB sessions — one failure doesn't kill others

## Phase 4: Deployment (Free Tier)
Objective: Hosted on Railway for zero cost.

- [x] Create Procfile + runtime.txt
- [x] Dockerfile with multi-stage build (Node → Python, Vite frontend bundled)
- [x] `railway.json` config (Dockerfile builder, auto-sleep)
- [x] `.env.example` with Railway notes
- [x] Port binding via `$PORT` env var (shell-form CMD)
- [x] Set up Railway project from GitHub
- [x] Configure environment variables in dashboard
- [ ] Run seed + initial ingest on Railway shell
- [ ] Set up custom domain (optional)
- [ ] Verify HTTPS, WebSocket, all endpoints work

## Phase 5: Observability
Objective: Know when things break.

- [x] Add structlog for structured JSON logging (ISO timestamps, log levels, colored console in dev, JSON in prod)
- [x] Add Sentry for error tracking (self-hosted or sentry.io — set `SENTRY_DSN`)
- [x] Log ingestion failures with reason (errors list in IngestionRun, per-feed logging)
- [x] Add Prometheus `/metrics` endpoint (`http_requests_total`, `http_request_duration_seconds` by method+path+status)
- [x] Request duration middleware across all routes
- [x] `LOG_LEVEL` env var (DEBUG|INFO|WARNING|ERROR)

## Phase 6: Security Hardening
Objective: Lock down the app for production.

- [x] WebSocket authentication — first message must be `{"type":"auth","token":"..."}`, reject with code 4001 otherwise
- [x] CORS origins configurable via `CORS_ORIGINS` env var (lock down in production)
- [x] Rate limiting with Redis fallback (`redis.asyncio` → DB if unavailable)
- [x] Security headers middleware — CSP, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, HSTS
- [x] All user inputs validated via Pydantic schemas / FastAPI type coercion
- [x] All admin routes protected by `require_admin` dependency
- [x] `@app.middleware("http")` instead of `BaseHTTPMiddleware` (WebSocket-safe)

## Phase 7: Frontend Build
Objective: Faster load times, smaller bundles.

- [x] Set up Vite or esbuild for JS/CSS bundling
- [x] Minify CSS/JS in build step
- [x] Add cache busting via content hashes (built-in)
- [x] Serve built assets via Nginx/CDN instead of FastAPI
- [x] Lazy-load non-critical JS

## Phase 8: CI/CD & Testing
Objective: Automated quality gates.

- [x] Add GitHub Actions: run tests on every push
- [x] Add GitHub Actions: lint with ruff
- [x] Add integration tests for auth flow (8 tests: register, login, refresh, profile, validation)
- [x] Add integration tests for article CRUD + bookmarks (8 tests: list, pagination, filter, single, 404, bookmark lifecycle, unauthorized)
- [x] Add E2E test for critical user path (5 Playwright tests: home, latest, category filter, article page, register+login)
- [ ] Auto-deploy to Railway on main branch push (Railway auto-deploys — needs Railway project setup)

## Phase 9: Features & Growth
Objective: User-facing improvements.

- [ ] Email verification on registration
- [ ] Password reset flow
- [ ] User preferences (theme, language, categories)
- [ ] "Mark as read" tracking
- [ ] Reading history page
- [ ] Push notifications for breaking news
- [ ] Mobile app wrapper (PWA or Capacitor)

---

## Deployment Quick Reference

```bash
# Local dev
source .venv/bin/activate
uvicorn backend.app:app --reload --port 8000

# Seed DB
python -m backend.seed

# Ingest feeds
python -c "import asyncio; from backend.services.news_service import ingest_feeds; asyncio.run(ingest_feeds())"

# Tests
python -m pytest tests/ -v

# Production (Docker)
docker compose up --build
```

## Key Files

| Path | Purpose |
|------|---------|
| `backend/app.py` | FastAPI entrypoint, routers, static mount |
| `backend/config.py` | All settings with env overrides |
| `backend/database/__init__.py` | Async engine, session factory |
| `backend/models/models.py` | SQLAlchemy models |
| `backend/auth/auth.py` | JWT + password hashing |
| `backend/routes/auth_routes.py` | Register, login, refresh |
| `backend/routes/news.py` | GET articles, search, pagination |
| `backend/services/news_service.py` | 62 RSS feeds, parallel ingestion |
| `backend/services/rate_limit.py` | DB-backed rate limiting |
| `backend/seed.py` | Seed categories + sources |
| `frontend/assets/js/api.js` | API client with JWT auto-refresh |
| `frontend/assets/js/app.js` | All page logic |
| `frontend/assets/js/layout.js` | Header, sidebar, theme toggle |
| `frontend/assets/css/variables.css` | All CSS vars + light/dark theme |
