"""Inline demo article seeder — avoids cross-package import issues."""
from datetime import datetime, timedelta

from sqlalchemy import select

from .database import async_session, init_db
from .models.models import Article, ArticleStatus, Category, Source


async def seed_demo_articles():
    await init_db()
    async with async_session() as db:
        cats = {c.slug: c for c in (await db.execute(select(Category))).scalars().all()}
        existing_sources = {s.name: s for s in (await db.execute(select(Source))).scalars().all()}

        country_sources = {
            "US": "ABC News", "UK": "BBC World", "India": "NDTV",
            "Germany": "Tagesschau", "France": "Le Monde",
        }

        articles_data = [
            ("US Markets Hit All-Time High on Tech Rally", "business", "US"),
            ("Federal Reserve Holds Interest Rates Steady", "business", "US"),
            ("NASA Announces New Mars Mission for 2028", "science", "US"),
            ("Major Earthquake Hits California Coast", "world", "US"),
            ("US Healthcare Bill Sparks Debate in Congress", "health", "US"),
            ("Hollywood Strikes: Studios Reach Agreement", "entertainment", "US"),
            ("Super Bowl LXI Sets Viewership Record", "sports", "US"),
            ("AI Startup Raises $5B in Record Funding Round", "technology", "US"),
            ("UK Prime Minister Announces New Cabinet", "world", "UK"),
            ("Premier League Season Preview: Top Contenders", "sports", "UK"),
            ("BBC Launches New Digital-First Strategy", "technology", "UK"),
            ("London Stock Exchange Reports Strong Quarter", "business", "UK"),
            ("NHS Winter Preparedness Plan Released", "health", "UK"),
            ("India Launches Chandrayaan-4 Moon Mission", "science", "India"),
            ("Indian Economy Grows 8.2% in Q2", "business", "India"),
            ("IPL 2026: New Teams and Format Announced", "sports", "India"),
            ("Digital India: 5G Coverage Reaches Rural Areas", "technology", "India"),
            ("Germany Approves Major Renewable Energy Package", "world", "Germany"),
            ("Bundesliga Season Kicks Off with Record Attendance", "sports", "Germany"),
            ("Volkswagen Unveils New Electric Vehicle Lineup", "business", "Germany"),
            ("France Hosts Global AI Safety Summit", "technology", "France"),
            ("French Wine Industry Reports Record Exports", "business", "France"),
            ("Tour de France 2026: Route Revealed", "sports", "France"),
        ]

        now = datetime.utcnow()
        added = 0
        for title, cat_slug, country in articles_data:
            existing = await db.execute(select(Article).where(Article.title == title))
            if existing.scalar_one_or_none():
                continue

            cat = cats.get(cat_slug)
            if not cat:
                continue

            src_name = country_sources.get(country)
            src = existing_sources.get(src_name)
            if not src:
                src = Source(name=src_name or f"{country} News", country=country, feed_url="", is_active=True)
                db.add(src)
                await db.flush()
                existing_sources[src.name] = src

            a = Article(
                title=title,
                slug=f"demo-{added}-{title.lower().replace(' ', '-')[:60].rstrip('-')}",
                summary=f"{title}. This is a demo article for testing and display purposes.",
                content=f"Full article content about {title.lower()}. This is a demonstration article seeded for initial deployment.",
                status=ArticleStatus.PUBLISHED,
                category_id=cat.id,
                source_id=src.id,
                published_at=now - timedelta(hours=added),
            )
            db.add(a)
            added += 1

        await db.commit()
        print(f"Seeded {added} demo articles across 5 countries")
