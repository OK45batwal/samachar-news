import asyncio
import structlog

logger = structlog.get_logger(__name__)


async def background_ingestion_loop(interval_minutes: int = 30):
    """Periodically ingest and fact-check feeds in the background, updating DB, JSON dataset, and sitemap."""
    # Brief delay on startup to allow server to bind ports cleanly
    await asyncio.sleep(10)
    while True:
        try:
            logger.info("Starting scheduled feed ingestion and dataset update...")
            from scripts.cron_ingest import update_live_news_dataset
            count = await update_live_news_dataset()
            logger.info("Scheduled ingestion complete", verified_articles=count)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Scheduled ingestion encountered error", error=str(e))
        
        await asyncio.sleep(interval_minutes * 60)

