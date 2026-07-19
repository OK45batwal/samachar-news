# Priority Tracker — Samachar News

Legend: `🔴 critical` `🟡 high` `🟢 medium` `⚪ low` `✅ done`

## 🔴 Critical

| ID | Status | Type | What | Where |
|----|--------|------|------|-------|
| P-01 | ✅ | bug | `ingest_feeds` shares single `AsyncSession` across 60+ concurrent `asyncio.gather` tasks — SQLAlchemy async sessions aren't concurrency-safe. Pool sessions per feed or serialize. | `backend/services/news_service.py:355` |

## 🟡 High

| ID | Status | Type | What | Where |
|----|--------|------|------|-------|
| P-02 | ✅ | bug | Duplicate `from sqlalchemy import func, select` — imported at module top, re-imported inside `lifespan()`. | `backend/app.py:46` |
| P-03 | ✅ | feature | Bookmarks page shows empty state even when signed in. Removed stale in-memory CSRF validation that broke on server restart. | `backend/routes/bookmarks.py` |
| P-04 | | feature | Admin CRUD API has no frontend. Full article/user/category/source/ingestion management endpoints with zero UI consumers. | `backend/routes/admin_routes.py` |

## 🟢 Medium

| ID | Status | Type | What | Where |
|----|--------|------|------|-------|
| P-05 | ✅ | polish | Seed data reuses same 4 demo articles across 23 entries, 5 countries. Added country-specific intro. | `backend/seed_e2e_inline.py` |
| P-06 | ✅ | polish | `difflib.SequenceMatcher` fuzzy country matching runs O(n²) per `/geo` request. Removed entirely — alias-based exact match covers all realistic cases. | `backend/routes/news.py:70-99` |
| P-07 | ✅ | polish | Vite dev proxy proxies `/api` but not `/api/ws`. WebSocket connections in dev go to wrong port. | `vite.config.js` |
| P-08 | | feature | Forgot password page exists (`forgot-password.html`) but no backend endpoint. | `frontend/forgot-password.html` |
| P-09 | | feature | Profile page shows only username. No edit profile, avatar upload, or preferences UI. | `frontend/profile.html` |
| P-10 | ✅ | feature | WebSocket `subscribe`/`unsubscribe` handled in loop but never acted on. Removed dead handlers. | `backend/websocket/ws.py:96-98` |
| P-11 | ✅ | infra | CI skips Vite build — e2e serves raw HTML. Added `npm run build` step before e2e. | `.github/workflows/test.yml` |
| P-12 | ✅ | infra | Docker mentioned in README but no `Dockerfile` or `compose.yml` exists. Removed from tech stack table. | root |

## ⚪ Low

| ID | Status | Type | What | Where |
|----|--------|------|------|-------|
| P-13 | ✅ | polish | Emoji-based country flags limited to 18 countries in `map-init.js` while backend has 28. Unmatched countries show 🌐. | `frontend/src/js/map-init.js:13` |
| P-14 | ✅ | delete | `postcss.config.js` — empty `plugins: {}`, no PostCSS plugins used. | `postcss.config.js` |
| P-15 | ✅ | delete | `backend/seed_e2e_inline.py` and `scripts/seed_e2e.py` — nearly identical seed logic. Consolidate into one. | `backend/seed_e2e_inline.py` + `scripts/seed_e2e.py` |
| P-16 | | infra | Render `free` plan spins down after inactivity. Consider starter plan or health ping. | `render.yaml` |
| P-17 | ✅ | polish | `CATEGORY_CACHE` in `news_service.py` never invalidated — stale if admin adds categories at runtime. | `backend/services/news_service.py:102` |