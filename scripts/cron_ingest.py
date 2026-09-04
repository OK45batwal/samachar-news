"""
Continuous 24x7 Real-World News Ingestion & Dataset Updater.
Fetches breaking stories from 25+ global wire feeds, runs MEKA 3.0 Truth Engine,
and updates both the SQLite/Postgres DB and frontend/assets/data/news.json.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import async_session, init_db
from backend.models.models import Article, Category, Source
from backend.seed import seed_database
from backend.services.news_service import ingest_all_feeds
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("24x7_news_updater")


async def update_live_news_dataset(limit: int = 150):
    """Fetch live news from feeds and export updated dataset to frontend/assets/data/news.json."""
    logger.info("🔧 Ensuring database schema and base tables exist...")
    await init_db()
    await seed_database()

    logger.info("📡 Starting 24x7 Global News Wire Ingestion...")
    ingest_result = await ingest_all_feeds()
    logger.info(f"✅ Ingestion Complete: Fetched {ingest_result.get('fetched', 0)} stories, Created {ingest_result.get('created', 0)} new articles.")

    # Export to JSON dataset
    async with async_session() as db:
        res = await db.execute(select(Article).order_by(Article.published_at.desc()).limit(limit))
        articles = res.scalars().all()

        cat_res = await db.execute(select(Category))
        categories = {c.id: c.name for c in cat_res.scalars().all()}

        src_res = await db.execute(select(Source))
        sources = {s.id: s.name for s in src_res.scalars().all()}

        dataset = []
        for a in articles:
            dataset.append({
                "id": a.id,
                "title": a.title,
                "slug": a.slug,
                "summary": a.summary,
                "content": a.content,
                "image_url": a.image_url,
                "source_url": a.source_url,
                "author": a.author,
                "source_name": sources.get(a.source_id, "Wire Feed"),
                "category_name": categories.get(a.category_id, "General"),
                "published_at": a.published_at.isoformat() if a.published_at else "",
                "credibility_score": a.credibility_score,
                "sensationalism_score": a.sensationalism_score,
                "fact_check_status": a.fact_check_status.value if hasattr(a.fact_check_status, "value") else str(a.fact_check_status),
                "key_claims": a.key_claims,
                "corroborating_sources": a.corroborating_sources,
                "bias_spectrum": a.bias_spectrum,
            })

        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "data", "news.json"))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"🚀 Successfully written {len(dataset)} verified live news articles to {output_path}")
        return len(dataset)


async def run_continuous_loop(interval_minutes: int = 15):
    """Run continuously 24x7 in background."""
    logger.info(f"🔄 Starting 24x7 News Daemon (Interval: Every {interval_minutes} minutes)")
    while True:
        try:
            await update_live_news_dataset()
        except Exception as e:
            logger.error(f"❌ Error during scheduled news update: {e}", exc_info=True)
        await asyncio.sleep(interval_minutes * 60)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        asyncio.run(run_continuous_loop(15))
    else:
        asyncio.run(update_live_news_dataset())
