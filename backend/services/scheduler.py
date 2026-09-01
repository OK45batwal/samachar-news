import asyncio
import structlog
from .news_service import ingest_all_feeds

logger = structlog.get_logger(__name__)


async def background_ingestion_loop(interval_minutes: int = 30):
    """Periodically ingest and fact-check feeds in the background."""
    while True:
        try:
            await asyncio.sleep(interval_minutes * 60)
            logger.info("Starting scheduled feed ingestion...")
            result = await ingest_all_feeds()
            logger.info("Scheduled ingestion complete", result=result)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Scheduled ingestion failed", error=str(e))
            await asyncio.sleep(60)
