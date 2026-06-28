import asyncio
import feedparser
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import Article, Source, Category, ArticleStatus
from ..database import async_session
from ..utils.utils import slugify

logger = logging.getLogger(__name__)

FEED_URLS = {
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
    "cnn": "http://rss.cnn.com/rss/edition.rss",
    "reuters": "https://www.reutersagency.com/feed/",
    "aljazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}

async def fetch_article_content(url: str) -> Optional[str]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None

def _parse_feed(feed_url: str):
    return feedparser.parse(feed_url)

async def ingest_feeds():
    async with async_session() as db:
        for source_key, feed_url in FEED_URLS.items():
            try:
                feed = await asyncio.to_thread(_parse_feed, feed_url)
            except Exception as e:
                logger.error("Failed to parse feed %s: %s", feed_url, e)
                continue

            if feed.bozo and not feed.entries:
                logger.warning("Feed %s returned no entries (bozo=%s)", feed_url, feed.bozo)
                continue

            source_result = await db.execute(select(Source).where(Source.name == source_key))
            source = source_result.scalar_one_or_none()
            if not source:
                source = Source(name=source_key, feed_url=feed_url, is_active=True)
                db.add(source)
                await db.commit()
                await db.refresh(source)

            general_cat = await db.execute(select(Category).where(Category.slug == "general"))
            default_cat = general_cat.scalar_one_or_none()
            if not default_cat:
                default_cat = Category(name="General", slug="general")
                db.add(default_cat)
                await db.commit()
                await db.refresh(default_cat)

            for entry in feed.entries[:20]:
                link = entry.get("link", "")
                if not link:
                    continue

                existing = await db.execute(
                    select(Article).where(Article.source_url == link)
                )
                if existing.scalar_one_or_none():
                    continue

                raw_slug = slugify(entry.get("title", "")) or link.split("/")[-1][:200]
                slug_base = raw_slug[:200]
                slug = slug_base
                counter = 1
                while True:
                    slug_check = await db.execute(
                        select(Article).where(Article.slug == slug)
                    )
                    if not slug_check.scalar_one_or_none():
                        break
                    slug = f"{slug_base[:190]}-{counter}"
                    counter += 1

                published = None
                if entry.get("published_parsed"):
                    try:
                        published = datetime(*entry.get("published_parsed")[:6])
                    except Exception:
                        published = datetime.utcnow()

                article = Article(
                    title=entry.get("title", ""),
                    slug=slug,
                    summary=(entry.get("summary") or "")[:500],
                    content=(entry.get("content", [{}])[0].get("value", "")
                             if entry.get("content") else entry.get("summary", "")),
                    image_url=(
                        next(
                            (m.get("href", "")
                             for m in (entry.get("media_content") or [])
                             if m.get("href")),
                            ""
                        )
                    ),
                    source_url=link,
                    author=entry.get("author", ""),
                    status=ArticleStatus.PUBLISHED,
                    category_id=default_cat.id,
                    source_id=source.id,
                    published_at=published or datetime.utcnow(),
                )
                db.add(article)

        await db.commit()
        logger.info("Feed ingestion complete")
