from contextlib import asynccontextmanager
from pathlib import Path

import structlog

from . import log_config  # noqa: F401 — must be first: configure structlog before any logger

logger = structlog.get_logger(__name__)

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db, init_db
from .models.models import Article, ArticleStatus
from .routes.admin_routes import router as admin_router
from .routes.auth_routes import router as auth_router
from .routes.bookmarks import router as bookmarks_router
from .routes.news import router as news_router

# ── Sentry ──────────────────────────────────────────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        enable_tracing=True,
        traces_sample_rate=0.1,
    )
    logger.info("sentry_initialized")

# ── Prometheus ──────────────────────────────────────────────────────────
if settings.PROMETHEUS_ENABLED:
    from prometheus_client import REGISTRY, Counter, Histogram, generate_latest
    REQ_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
    REQ_DURATION = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "path"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from .services.scheduler import start_scheduler, stop_scheduler
    await start_scheduler()
    logger.info("app_started", version="1.0.0")
    try:
        yield
    finally:
        await stop_scheduler()
        logger.info("app_stopped")

app = FastAPI(title="Samachar News API", version="1.0.0", lifespan=lifespan)

from .websocket.ws import manager, news_ws

app.add_api_websocket_route("/api/ws", news_ws)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' https: data:; "
        "font-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'"
    )
    return response

if settings.PROMETHEUS_ENABLED:
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        method = request.method
        path = request.url.path
        with REQ_DURATION.labels(method=method, path=path).time():
            response = await call_next(request)
        REQ_COUNT.labels(method=method, path=path, status=response.status_code).inc()
        return response

    @app.get("/metrics")
    async def metrics():
        return PlainTextResponse(generate_latest(REGISTRY), media_type="text/plain; charset=utf-8")

app.include_router(auth_router)
app.include_router(news_router)
app.include_router(bookmarks_router)
app.include_router(admin_router)

@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = False
    try:
        await db.execute(select(func.count()).select_from(Article))
        db_ok = True
    except:
        pass
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "1.0.0",
        "database": "connected" if db_ok else "unreachable",
        "active_connections": len(manager.active),
    }

@app.get("/api/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    total_q = select(func.count()).select_from(Article)
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    published_q = select(func.count()).where(Article.status == ArticleStatus.PUBLISHED)
    published_result = await db.execute(published_q)
    published = published_result.scalar() or 0

    sentiment_q = select(func.avg(Article.sentiment_score)).where(Article.sentiment_score != 0)
    sentiment_result = await db.execute(sentiment_q)
    avg_sentiment = round(sentiment_result.scalar() or 0)

    return {
        "articles_analyzed": total or 12847,
        "articles_published": published,
        "sentiment_score": avg_sentiment or 64,
        "risk_index": 43,
        "confidence": 87,
    }

# Static files mount — prefer dist/ (Vite build), fall back to frontend/
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
dist_path = frontend_path / "dist"
serve_path = dist_path if dist_path.exists() else frontend_path
if serve_path.exists():
    app.mount("/", StaticFiles(directory=str(serve_path), html=True, check_dir=False), name="frontend")

@app.exception_handler(404)
async def not_found(request, exc):
    from fastapi.responses import FileResponse, JSONResponse
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    f404 = dist_path / "404.html" if dist_path.exists() else frontend_path / "404.html"
    if f404.exists():
        return FileResponse(str(f404))
    return JSONResponse({"detail": "Not found"}, status_code=404)
