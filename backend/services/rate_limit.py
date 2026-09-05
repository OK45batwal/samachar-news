import time
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.models import RateLimitEntry

WINDOW_SECONDS = 60
_LAST_CLEANUP_TS: float = 0.0


async def check_rate_limit(key: str, db: AsyncSession) -> None:
    """DB-backed sliding window rate limiter with throttled background cleanup."""
    global _LAST_CLEANUP_TS
    limit = settings.RATE_LIMIT_PER_MINUTE
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)

    try:
        current_time = time.time()
        if current_time - _LAST_CLEANUP_TS > 60:
            await db.execute(delete(RateLimitEntry).where(RateLimitEntry.timestamp < cutoff))
            _LAST_CLEANUP_TS = current_time

        result = await db.execute(
            select(RateLimitEntry).where(
                RateLimitEntry.key == key,
                RateLimitEntry.timestamp >= cutoff,
            )
        )
        recent = result.scalars().all()

        if len(recent) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

        db.add(RateLimitEntry(key=key, timestamp=now))
        await db.commit()
    except HTTPException:
        raise
    except Exception:
        await db.rollback()


async def rate_limit(request: Request, db: AsyncSession) -> None:
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{request.url.path}"
    await check_rate_limit(key, db)
