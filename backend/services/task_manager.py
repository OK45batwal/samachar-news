import asyncio
from datetime import datetime
from typing import Optional

import structlog

from ..database import async_session
from ..models.models import IngestionRun

logger = structlog.get_logger(__name__)

_running_tasks: dict[str, asyncio.Task] = {}


async def start_ingestion() -> str:
    run = IngestionRun(
        status="running",
        total_feeds=0,
        feeds_succeeded=0,
        feeds_failed=0,
        articles_added=0,
        errors=[],
    )
    async with async_session() as db:
        db.add(run)
        await db.commit()
        run_id = run.id

    task = asyncio.create_task(_do_ingest(run_id))
    _running_tasks[run_id] = task
    return run_id


async def _do_ingest(run_id: str):
    from ..services.news_service import FEED_CONFIG, _get_category, _get_source, _ingest_feed

    async with async_session() as db:
        total = len(FEED_CONFIG)
        succeeded = 0
        failed = 0
        articles = 0
        errors = []

        # Seed categories first
        category_defs = [
            ("General", "general"), ("World", "world"), ("Technology", "technology"),
            ("Business", "business"), ("Sports", "sports"), ("Science", "science"),
            ("Health", "health"), ("Politics", "politics"), ("Entertainment", "entertainment"),
        ]
        for name, slug in category_defs:
            cat = await _get_category(db, slug)
            if not cat:
                from ..models.models import Category
                db.add(Category(name=name, slug=slug, description=f"{name} news", icon=slug))
        await db.commit()

        # Seed sources sequentially to avoid race conditions
        for key, cfg in FEED_CONFIG.items():
            try:
                await _get_source(db, key, cfg)
            except Exception as e:
                logger.warning("Seed %s failed: %s", key, e)
        await db.commit()

        async def _run_feed(key: str, cfg: dict) -> int:
            try:
                async with async_session() as feed_db:
                    count = await _ingest_feed(feed_db, key, cfg) or 0
                    await feed_db.commit()
                    return count
            except Exception as e:
                logger.warning("Feed %s failed: %s", key, e)
                return 0

        tasks = [_run_feed(key, cfg) for key, cfg in FEED_CONFIG.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            key = list(FEED_CONFIG.keys())[i]
            if isinstance(result, Exception):
                failed += 1
                errors.append({"feed": key, "error": str(result)})
                logger.warning("Feed %s failed: %s", key, result)
            elif result is not None and result > 0:
                articles += result
                succeeded += 1
            else:
                failed += 1

        run = await db.get(IngestionRun, run_id)
        if run:
            run.status = "completed"
            run.total_feeds = total
            run.feeds_succeeded = succeeded
            run.feeds_failed = failed
            run.articles_added = articles
            run.errors = errors
            run.completed_at = datetime.utcnow()
            await db.commit()

        logger.info(
            "Ingestion %s: %d new articles from %d/%d sources",
            run_id[:8], articles, succeeded, total,
        )

    _running_tasks.pop(run_id, None)


async def get_ingestion_status(run_id: str) -> Optional[dict]:
    async with async_session() as db:
        run = await db.get(IngestionRun, run_id)
        if not run:
            return None
        return {
            "id": run.id,
            "status": run.status,
            "total_feeds": run.total_feeds,
            "feeds_succeeded": run.feeds_succeeded,
            "feeds_failed": run.feeds_failed,
            "articles_added": run.articles_added,
            "errors": run.errors,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }


async def get_last_ingestion() -> Optional[dict]:
    async with async_session() as db:
        from sqlalchemy import desc, select
        result = await db.execute(
            select(IngestionRun).order_by(desc(IngestionRun.started_at)).limit(1)
        )
        run = result.scalar_one_or_none()
        if not run:
            return None
        return {
            "id": run.id,
            "status": run.status,
            "total_feeds": run.total_feeds,
            "feeds_succeeded": run.feeds_succeeded,
            "feeds_failed": run.feeds_failed,
            "articles_added": run.articles_added,
            "errors": run.errors,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }
