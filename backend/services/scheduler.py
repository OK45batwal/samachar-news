import asyncio

import structlog

logger = structlog.get_logger(__name__)

_scheduler_task: asyncio.Task | None = None
_INTERVAL_SECONDS = 1800  # 30 minutes


async def start_scheduler():
    global _scheduler_task
    if _scheduler_task is not None:
        return
    _scheduler_task = asyncio.create_task(_run_scheduler())
    logger.info("Scheduler started (interval=%ds)", _INTERVAL_SECONDS)


async def stop_scheduler():
    global _scheduler_task
    if _scheduler_task is None:
        return
    _scheduler_task.cancel()
    try:
        await _scheduler_task
    except asyncio.CancelledError:
        pass
    _scheduler_task = None
    logger.info("Scheduler stopped")


async def _run_scheduler():
    while True:
        try:
            await asyncio.sleep(_INTERVAL_SECONDS)
            from .task_manager import start_ingestion
            run_id = await start_ingestion()
            logger.info("Scheduled ingestion started: %s", run_id[:8])
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Scheduled ingestion failed: %s", e)
