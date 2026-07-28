# Samachar News — AI Agent Knowledge Base & Architectural Blueprint (`brain.md`)

This document serves as a single-source-of-truth knowledge base and architectural blueprint for the **Samachar News** platform. Any AI agent or developer working on this codebase should consult this file first to understand the system architecture, component relationships, data flow, key files, and technical backlog without needing to re-scan the entire codebase.

---

## 1. Executive Summary & Tech Stack

**Samachar News** is a full-stack, real-time news intelligence platform. It automatically ingests articles from 50+ international and regional RSS feeds, processes text through AI algorithms (sentiment analysis, TF-IDF topic extraction, risk indexing, and content recommendations), tracks country-level geopolitical news on an interactive map, and streams breaking updates via WebSockets.

### Tech Stack Matrix
| Layer | Technologies / Tools |
| :--- | :--- |
| **Backend Framework** | Python 3.10+ / FastAPI, Uvicorn / Gunicorn |
| **Database & ORM** | SQLAlchemy 2.0 (AsyncIO), SQLite (`samachar.db`) for dev, PostgreSQL for prod, Alembic migrations |
| **Authentication** | Custom JWT (python-jose, bcrypt) with HttpOnly + Secure cookies & CSRF tokens |
| **Background Tasks** | Lightweight `asyncio` Task Manager & periodic Background Scheduler (no Celery needed) |
| **AI & NLP** | TextBlob (Sentiment Analysis), Scikit-learn (TF-IDF & Cosine Similarity Recommendations), NumPy |
| **Frontend UI** | Vanilla HTML5 / CSS3 (CSS Variables, Flexbox/Grid), Modern JS (ES Modules) |
| **Frontend Tooling** | Vite (Dev proxy & CSS/JS bundling/minification) |
| **Integrations & Maps**| Leaflet.js (Geopolitical map), Chart.js (AI Sentiment Analytics), WebSockets (`ws://`) |
| **Observability** | Structlog (Structured JSON logging), Prometheus (`/metrics`), Sentry (Error tracking) |
| **Container & Cloud** | Docker, Docker Compose, Render (`render.yaml`, `Procfile`) |
| **CI / CD** | GitHub Actions (`.github/workflows/test.yml`), Pytest, Playwright E2E |

---

## 2. Repository Directory Structure

```
samachar-news/
├── backend/                  # FastAPI Application Core
│   ├── ai/                   # AI & Data Science modules
│   │   └── ai_service.py     # Sentiment analysis, TF-IDF trending, risk index, recommendations
│   ├── auth/                 # Authentication modules
│   │   ├── auth.py           # Custom JWT auth, password hashing, get_current_user dependency
│   │   └── supertokens.py    # Optional SuperTokens auth integration (legacy/inactive)
│   ├── database/             # Database initialization & session management
│   │   └── __init__.py       # Async engine, sessionmaker, get_db dependency
│   ├── models/               # SQLAlchemy ORM Models
│   │   └── models.py         # User, Category, Source, Article, Bookmark, IngestionRun, RateLimitEntry
│   ├── routes/               # API Route Handlers
│   │   ├── admin_routes.py   # Admin management endpoints (dashboard, CRUD) [Unregistered in app.py]
│   │   ├── auth_routes.py    # User registration, login, logout, me, ws-token
│   │   ├── bookmarks.py     # User bookmark CRUD handlers
│   │   └── news.py           # Public news endpoints, geo-map, search, article detail
│   ├── services/             # Core Business Logic & Infrastructure Services
│   │   ├── feed_parser.py    # RSS XML parsing fallback logic
│   │   ├── news_service.py   # FEED_CONFIG (50+ RSS feeds) & async feed ingestion engine
│   │   ├── rate_limit.py     # DB-backed sliding window rate limiter
│   │   ├── scheduler.py      # 30-minute periodic ingestion scheduler
│   │   └── task_manager.py  # Background ingestion task queue & IngestionRun tracker
│   ├── utils/                # Helper utilities
│   │   └── utils.py          # Slugification, text helpers
│   ├── websocket/            # Realtime WebSockets
│   │   └── ws.py             # ConnectionManager & /api/ws endpoint handler
│   ├── app.py                # FastAPI main entrypoint, middleware, lifespan, static mounting
│   ├── config.py             # Pydantic Settings & environment configuration loader
│   ├── log_config.py         # Structlog configuration setup
│   ├── schemas.py            # Pydantic input/output validation schemas
│   └── seed.py               # Database initial seeder (categories & sources)
│
├── frontend/                 # Frontend Web Application
│   ├── assets/               # Static assets & JS logic
│   │   ├── css/              # Stylesheets (variables.css, style.css, components)
│   │   ├── js/
│   │   │   ├── api.js        # Central API client (fetch wrapper, token injection, error handling)
│   │   │   ├── app.js        # Main UI rendering engine, WS client, bookmarks, search modal
│   │   │   └── layout.js     # Shared header/footer layout injector & active nav state
│   │   └── fonts/, icons/, images/
│   ├── src/js/               # Page-specific frontend JS scripts
│   │   ├── main.js           # Shared page bootstrapper
│   │   └── map-init.js       # Leaflet global news map initializer
│   ├── index.html            # Landing / Hero page
│   ├── home.html             # Personalized user feed dashboard
│   ├── latest.html           # Real-time article stream with search & filters
│   ├── article.html          # Full article reader view with sentiment & recommendations
│   ├── map.html              # Geopolitical intelligence map
│   ├── trending.html         # Hot topics & risk metrics dashboard
│   ├── ai.html               # AI analytics hub & sentiment overview
│   ├── bookmarks.html        # Saved articles manager
│   ├── history.html          # User reading history log
│   ├── profile.html          # User profile view (frontend placeholder)
│   ├── login.html            # Authentication login UI
│   ├── register.html         # User sign-up UI
│   ├── forgot-password.html  # Password recovery UI (missing backend endpoint)
│   ├── about.html, contact.html, privacy.html, 404.html
│   └── dist/                 # Vite production build output (when generated)
│
├── alembic/                  # Database migration scripts
├── scripts/                  # E2E seeding & deployment helper scripts
├── tests/                    # Pytest backend integration unit tests & Playwright E2E tests
│   ├── e2e/                  # Playwright browser end-to-end test suite
│   ├── conftest.py           # Test fixtures & async client configuration
│   └── test_*.py             # Test files for auth, content, models, utils
├── Dockerfile                # Production Docker container image definition
├── docker-compose.yml        # Docker Multi-container setup (App + PostgreSQL + Redis)
├── render.yaml               # Render free-tier deployment specification
├── vite.config.js            # Vite bundler & development proxy server configuration
├── pyproject.toml            # Python tool configuration (Ruff, Pytest)
├── requirements.txt          # Python dependencies
└── package.json              # Node.js dependencies & build scripts
```

---

## 3. Core Architecture & Subsystem Workflows

### A. Authentication & Session Flow
1. **Login (`POST /api/auth/login`)**: Validates credentials using `bcrypt`. Generates a JWT access token and sets it as an `HttpOnly` cookie (`access_token`). Generates a CSRF token stored in a non-HttpOnly cookie (`csrf_token`) and in an in-memory dictionary.
2. **Authenticated Requests**: Frontend `api.js` includes `credentials: 'include'` and sends `X-CSRF-Token` header on mutating requests (`POST`, `PUT`, `DELETE`). Backend `get_current_user` extracts JWT from cookie or `Authorization: Bearer` header.
3. **WebSocket Connection (`/api/ws`)**: Authenticated by fetching a 5-minute ephemeral token via `GET /api/auth/ws-token`, then sending `{ type: "auth", token: "..." }` as the first WebSocket message.

### B. News Ingestion Pipeline
1. `backend/services/scheduler.py` runs a 30-minute interval loop invoking `start_ingestion()`.
2. `start_ingestion()` creates an `IngestionRun` record in `ingestion_runs` table with `status="running"`.
3. Ingests 50+ RSS feeds defined in `FEED_CONFIG` in parallel using `httpx.AsyncClient` and `feedparser`.
4. For each article:
   - Computes TextBlob sentiment score (-100 to +100).
   - Generates URL slug and deduplicates based on `source_url`.
   - Stores article in `articles` table associated with `categories` and `sources`.
5. Updates `IngestionRun` with `completed_at`, `articles_added`, and any captured `errors`.

### C. Geopolitical Map & AI Analytics Subsystem
- **Map Data Endpoint (`GET /api/news/geo`)**: Aggregates published articles by `Source.country`, calculates average sentiment, extracts top keywords from article titles, and matches coordinate locations from `COUNTRY_COORDS`.
- **AI Analytics (`backend/ai/ai_service.py`)**:
  - `analyze_sentiment`: Aggregates sentiment distribution across article sets.
  - `find_trending_topics`: Uses `TfidfVectorizer(ngram_range=(1,2))` to identify dominant keywords.
  - `compute_risk_index`: Scans content for risk keywords (`conflict`, `crisis`, `attack`, `sanction`) to evaluate geopolitical instability scores.
  - `recommend_articles`: Computes Cosine Similarity between user reading history vectors and available article candidate vectors.

---

## 4. Primary Data Models & Schemas

| Table Name | Entity Model Class | Key Columns & Descriptions | Relationships |
| :--- | :--- | :--- | :--- |
| `users` | `User` | `id` (UUID string PK), `email` (unique index), `username` (unique index), `hashed_password`, `full_name`, `role` (`user`/`editor`/`admin`), `is_active` (bool), `preferences` (JSON) | `bookmarks` (1-to-N cascade delete) |
| `categories` | `Category` | `id` (Int PK), `name` (unique), `slug` (unique), `description`, `icon` | `articles` (1-to-N) |
| `sources` | `Source` | `id` (Int PK), `name`, `url`, `feed_url`, `country`, `language`, `is_active` | `articles` (1-to-N) |
| `articles` | `Article` | `id` (Int PK), `title`, `slug` (unique index), `summary`, `content`, `image_url`, `source_url` (unique), `author`, `status` (`draft`/`published`/`archived`), `view_count`, `sentiment_score`, `category_id` (FK), `source_id` (FK), `published_at` | `category`, `source`, `bookmarks` |
| `bookmarks` | `Bookmark` | `id` (Int PK), `user_id` (FK `users.id`), `article_id` (FK `articles.id`), `folder` (default: "default"), `created_at` | `user`, `article` |
| `ingestion_runs`| `IngestionRun` | `id` (UUID PK), `status` (`running`/`completed`/`failed`), `total_feeds`, `feeds_succeeded`, `feeds_failed`, `articles_added`, `errors` (JSON), `started_at`, `completed_at` | Standalone operational log |
| `rate_limits` | `RateLimitEntry` | `id` (Int PK), `key` (IP/endpoint string index), `timestamp` | Standalone sliding window log |

---

## 5. List of Technical Improvements & Needed Enhancements

The following categorized list details all known bugs, vulnerabilities, missing features, and technical debt items requiring resolution in future development work.

### 🔴 Critical Priority (Security & System Stability) — All Resolved ✅
1. **Unregistered Admin Routes & Dependency Mismatch**: [RESOLVED ✅]
   - **Location**: `backend/app.py` & `backend/routes/admin_routes.py`
   - **Fix Applied**: Updated `admin_routes.py` to import `get_current_user` from `backend.auth.auth` and registered `admin_router` in `backend/app.py`.

2. **Stored Cross-Site Scripting (XSS) Protection**: [RESOLVED ✅]
   - **Location**: `frontend/assets/js/app.js`
   - **Fix Applied**: Verified dynamic text escaping via `sanitize()` across article cards and detail rendering.

3. **In-Memory CSRF Storage Loss on Restart**: [RESOLVED ✅]
   - **Location**: `backend/routes/auth_routes.py`
   - **Fix Applied**: Upgraded CSRF tokens to HMAC-signed stateless tokens (`raw.signature`) with signature verification fallback, preventing token loss on server restarts.

4. **Dynamic Cookie `secure` Flag**: [RESOLVED ✅]
   - **Location**: `backend/routes/auth_routes.py`
   - **Fix Applied**: Replaced hardcoded `secure=True` with dynamic `_is_secure(request)` evaluation.

### 🟡 High Priority (Missing Features & UX Gaps) — All Resolved ✅
5. **Cosmetic-Only Forgot Password Page**: [RESOLVED ✅]
   - **Location**: `frontend/forgot-password.html` & `backend/routes/auth_routes.py`
   - **Fix Applied**: Implemented `/api/auth/forgot-password` and `/api/auth/reset-password` endpoints and connected `forgot-password.html`.

6. **Incomplete User Profile Page & Preferences**: [RESOLVED ✅]
   - **Location**: `frontend/profile.html` & `backend/routes/auth_routes.py`
   - **Fix Applied**: Added `PUT /api/auth/me` profile update endpoint and built Account Settings form in `profile.html`.

7. **WebSocket Port Proxying in Vite Dev Server**: [RESOLVED ✅]
   - **Location**: `vite.config.js`
   - **Fix Applied**: Configured `ws: true` under server proxy settings for `/api`.

### 🟢 Medium Priority (Performance & Architecture Polish)
9. **Category Cache Invalidation**:
   - **Location**: `backend/services/news_service.py` (`CATEGORY_CACHE`)
   - **Issue**: Category lookup maps are cached infinitely in memory. If an administrator adds a new category at runtime, the background ingestion service will not recognize it without a restart.
   - **Fix**: Implement cache time-to-live (TTL) or explicit cache invalidation when categories are modified.

10. **Database Connection Overhead in Rate Limiting**:
    - **Location**: `backend/services/rate_limit.py`
    - **Issue**: In the absence of Redis, every request executes an `INSERT` and `DELETE` on the SQLite/PostgreSQL `rate_limits` table, creating database write overhead.
    - **Fix**: Implement an in-memory sliding window fallback for single-instance deployments or ensure Redis is used in production.

11. **Render Free Tier Spin-Down Resilience**:
    - **Location**: `render.yaml`
    - **Issue**: On Render free tier, web instances sleep after 15 minutes of inactivity, delaying background RSS ingestion schedule.
    - **Fix**: Add a self-ping background worker or external cron ping (e.g., UptimeRobot) to keep ingestion active.

### ⚪ Low Priority & Code Hygiene
12. **Duplicate Seed Script Logic**:
    - **Location**: `backend/seed_e2e_inline.py` vs `scripts/seed_e2e.py`
    - **Issue**: Near-identical seed logic is duplicated across two files.
    - **Fix**: Consolidate seeding into a single module inside `backend/seed.py`.

13. **Dead Code Cleanup**:
    - **Location**: `backend/auth/supertokens.py`
    - **Issue**: Unused SuperTokens helper functions remain in the codebase while native JWT auth is used everywhere else.
    - **Fix**: Either fully integrate SuperTokens or remove `supertokens.py` to minimize maintenance overhead.

---

## 6. Developer & AI Agent Quick Reference Cheat-Sheet

### Commands to Run and Test

```bash
# 1. Install Dependencies
pip install -r requirements.txt
npm install

# 2. Run Backend Server (FastAPI Uvicorn)
uvicorn backend.app:app --reload --port 8000

# 3. Run Frontend Dev Server (Vite)
npm run dev

# 4. Run Pytest Backend Integration Tests
pytest

# 5. Run Playwright End-to-End Tests
npx playwright test

# 6. Database Migrations (Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head

# 7. Run Docker Environment
docker-compose up --build
```

### Environment Variables (.env)
```ini
DATABASE_URL=sqlite+aiosqlite:///./samachar.db
REDIS_URL=redis://localhost:6379/0
SAMACHAR_SECRET_KEY=your_super_secret_jwt_key
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173
PROMETHEUS_ENABLED=True
SENTRY_DSN=
```

---
*End of Knowledge Base — Last updated: July 2026*
