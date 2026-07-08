"""Seed test data for e2e tests. Usage: python scripts/seed_e2e.py"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from backend.database import async_session, init_db
from backend.models.models import Article, ArticleStatus, Category, Source


async def main():
    await init_db()
    async with async_session() as db:
        cats = {}
        for name, slug in [("General", "general"), ("Technology", "technology"), ("World", "world")]:
            existing = await db.execute(select(Category).where(Category.slug == slug))
            cat = existing.scalar_one_or_none()
            if not cat:
                cat = Category(name=name, slug=slug)
                db.add(cat)
                await db.flush()
            cats[slug] = cat

        existing = await db.execute(select(Source).where(Source.name == "Test Source"))
        src = existing.scalar_one_or_none()
        if not src:
            src = Source(name="Test Source", feed_url="https://example.com/rss")
            db.add(src)
            await db.flush()

        now = datetime.now(timezone.utc)
        for i, (title, cat_slug) in enumerate([
            ("Global Markets Rally on Tech Earnings", "general"),
            ("AI Regulation Framework Approved by EU", "technology"),
            ("Breakthrough in Quantum Computing", "technology"),
            ("Climate Summit 2026: Key Highlights", "world"),
            ("India Wins Cricket World Cup", "general"),
        ]):
            existing = await db.execute(select(Article).where(Article.title == title))
            if not existing.scalar_one_or_none():
                a = Article(
                    title=title,
                    slug=f"e2e-{i}-{title.lower().replace(' ', '-')[:50]}",
                    summary=f"Summary of {title}",
                    content=f"Full content about {title}.",
                    status=ArticleStatus.PUBLISHED,
                    category_id=cats[cat_slug].id,
                    source_id=src.id,
                    published_at=now,
                )
                db.add(a)

        await db.commit()
        print("Seed data created")


asyncio.run(main())
