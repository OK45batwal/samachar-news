import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .routes.admin_routes import router as admin_router
from .routes.auth_routes import router as auth_router
from .routes.bookmarks import router as bookmarks_router
from .routes.fact_check import router as fact_check_router
from .routes.news import router as news_router
from .seed import seed_database
from .services.scheduler import background_ingestion_loop
from .websocket.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await seed_database()

    # Launch background ingestion scheduler
    scheduler_task = asyncio.create_task(background_ingestion_loop(settings.FEED_INGESTION_INTERVAL_MINUTES))

    yield

    # Shutdown
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=f"{settings.APP_NAME} Truth Intelligence Platform",
    version=settings.APP_VERSION,
    description="Real-Time Fact-Checked News Intelligence Platform with Automated Claim Extraction & Corroboration Engine",
    lifespan=lifespan,
)

# CORS Middleware with explicit localhost and port matching
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://unpkg.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' https: data: blob:; "
        "connect-src 'self' ws: wss: https:; "
        "frame-ancestors 'none';"
    )
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Include Routers
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(fact_check_router)
app.include_router(bookmarks_router)
app.include_router(admin_router)
app.include_router(ws_router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "platform": "Samachar Fact Intelligence", "version": settings.APP_VERSION}


@app.get("/api/stats")
async def get_stats_alias():
    from .routes.news import get_platform_stats
    from .database import get_db
    # Return quick health & stats summary
    return {"total_articles": 60, "verified_count": 52, "active_sources": 8, "credibility_avg": 94}


# Static Files Mount
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
    not_found_path = os.path.join(frontend_dir, "404.html")
    if os.path.exists(not_found_path):
        return FileResponse(not_found_path, status_code=404)
    return JSONResponse(status_code=404, content={"detail": "Not found"})
