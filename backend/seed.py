"""Seed the database with initial categories and sources."""
import asyncio

from sqlalchemy import select

from .database import async_session, init_db
from .models.models import Category, Source
from .services.news_service import FEED_CONFIG


async def seed():
    await init_db()
    async with async_session() as db:
        category_defs = [
            ("General", "general", "General news", "general"),
            ("World", "world", "World news", "world"),
            ("Technology", "technology", "Technology news", "tech"),
            ("Business", "business", "Business and finance", "business"),
            ("Sports", "sports", "Sports news", "sports"),
            ("Science", "science", "Science and nature", "science"),
            ("Health", "health", "Health and medical", "health"),
            ("Politics", "politics", "Political news", "politics"),
            ("Entertainment", "entertainment", "Entertainment", "entertainment"),
        ]
        for name, slug, desc, icon in category_defs:
            existing = await db.execute(select(Category).where(Category.slug == slug))
            if not existing.scalar_one_or_none():
                db.add(Category(name=name, slug=slug, description=desc, icon=icon))

        for key, cfg in FEED_CONFIG.items():
            existing = await db.execute(select(Source).where(Source.name == cfg["name"]))
            if existing.scalar_one_or_none():
                continue
            db.add(Source(
                name=cfg["name"],
                feed_url=cfg["url"],
                country=cfg.get("country", ""),
                language=cfg.get("language", "en"),
                is_active=True,
            ))

        await db.commit()

        cats = (await db.execute(select(Category))).scalars().all()
        srcs = (await db.execute(select(Source))).scalars().all()
        print(f"Database seeded: {len(cats)} categories + {len(srcs)} sources")


if __name__ == "__main__":
    asyncio.run(seed())
