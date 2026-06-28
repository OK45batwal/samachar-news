"""Seed the database with initial categories and sources."""
import asyncio
from .database import async_session, init_db
from .models.models import Category, Source


async def seed():
    await init_db()
    async with async_session() as db:
        categories = [
            Category(name="General", slug="general", description="General news", icon="general"),
            Category(name="World", slug="world", description="World news", icon="world"),
            Category(name="Technology", slug="technology", description="Technology news", icon="tech"),
            Category(name="Business", slug="business", description="Business and finance", icon="business"),
            Category(name="Sports", slug="sports", description="Sports news", icon="sports"),
            Category(name="Science", slug="science", description="Science and nature", icon="science"),
            Category(name="Health", slug="health", description="Health and medical", icon="health"),
            Category(name="Politics", slug="politics", description="Political news", icon="politics"),
            Category(name="Entertainment", slug="entertainment", description="Entertainment", icon="entertainment"),
        ]
        for cat in categories:
            db.add(cat)

        sources = [
            Source(name="bbc", url="https://www.bbc.com/news", feed_url="http://feeds.bbci.co.uk/news/rss.xml", country="UK", language="en"),
            Source(name="cnn", url="https://www.cnn.com", feed_url="http://rss.cnn.com/rss/edition.rss", country="US", language="en"),
            Source(name="reuters", url="https://www.reuters.com", feed_url="https://www.reutersagency.com/feed/", country="UK", language="en"),
            Source(name="aljazeera", url="https://www.aljazeera.com", feed_url="https://www.aljazeera.com/xml/rss/all.xml", country="Qatar", language="en"),
        ]
        for src in sources:
            db.add(src)

        await db.commit()
        print("Database seeded: 9 categories + 4 sources")

if __name__ == "__main__":
    asyncio.run(seed())
