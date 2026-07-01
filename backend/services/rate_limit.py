from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.models import RateLimitEntry

WINDOW_SECONDS = 60

_redis = None
_redis_available = None


def _get_redis():
    global _redis, _redis_available
    if _redis_available is False:
        return None
    if _redis is not None:
        return _redis
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        _redis_available = True
        return _redis
    except Exception:
        _redis_available = False
        return None


async def _check_redis(key: str, limit: int) -> Optional[bool]:
    r = _get_redis()
    if r is None:
        return None
    try:
        now = int(datetime.now(timezone.utc).timestamp())
        window_start = now - WINDOW_SECONDS
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, WINDOW_SECONDS)
        _, count, *_ = await pipe.execute()
        return count >= limit
    except Exception:
        return None


async def check_rate_limit(key: str, db: AsyncSession) -> None:
    limit = settings.RATE_LIMIT_PER_MINUTE
    blocked = await _check_redis(key, limit)
    if blocked is True:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    if blocked is False:
        return

    # Fallback: DB-backed rate limiting
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)

    await db.execute(
        delete(RateLimitEntry).where(RateLimitEntry.timestamp < cutoff)
    )

    result = await db.execute(
        select(RateLimitEntry).where(
            RateLimitEntry.key == key,
            RateLimitEntry.timestamp >= cutoff,
        )
    )
    recent = result.scalars().all()

    if len(recent) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")

    db.add(RateLimitEntry(key=key, timestamp=now))
    await db.commit()


async def rate_limit(request: Request, db: AsyncSession) -> None:
    key = f"{request.client.host}:{request.url.path}"
    await check_rate_limit(key, db)
