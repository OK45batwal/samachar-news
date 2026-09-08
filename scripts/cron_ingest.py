"""
Continuous 24x7 Real-World News Ingestion & Dataset Updater.
Fetches breaking stories from 25+ global wire feeds, runs MEKA 3.0 Truth Engine,
and updates both the SQLite/Postgres DB and frontend/assets/data/news.json.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import async_session, init_db
from backend.models.models import Article, Category, Source
from backend.seed import seed_database
from backend.services.news_service import ingest_all_feeds, pick_topic_fallback_image
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("24x7_news_updater")


async def update_live_news_dataset(limit: int = 150):
    """Fetch live news from feeds and export updated dataset to frontend/assets/data/news.json."""
    logger.info("🔧 Ensuring database schema and base tables exist...")
    await init_db()
    await seed_database()

    logger.info("📡 Starting 24x7 Global News Wire Ingestion...")
    ingest_result = await ingest_all_feeds()
    logger.info(f"✅ Ingestion Complete: Fetched {ingest_result.get('fetched', 0)} stories, Created {ingest_result.get('created', 0)} new articles.")

    # Export to JSON dataset
    async with async_session() as db:
        res = await db.execute(select(Article).order_by(Article.published_at.desc()).limit(limit))
        articles = res.scalars().all()

        cat_res = await db.execute(select(Category))
        categories = {c.id: c.name for c in cat_res.scalars().all()}

        src_res = await db.execute(select(Source))
        sources = {s.id: s.name for s in src_res.scalars().all()}

        dataset = []
        modified = False
        for a in articles:
            cat_name = categories.get(a.category_id, "General")
            img = a.image_url
            if not img:
                img = pick_topic_fallback_image(a.title, a.summary or "", cat_name)
                a.image_url = img
                modified = True

            dataset.append({
                "id": a.id,
                "title": a.title,
                "slug": a.slug,
                "summary": a.summary,
                "content": a.content,
                "image_url": img,
                "source_url": a.source_url,
                "author": a.author,
                "source_name": sources.get(a.source_id, "Wire Feed"),
                "category_name": cat_name,
                "published_at": a.published_at.isoformat() if a.published_at else "",
                "credibility_score": a.credibility_score,
                "sensationalism_score": a.sensationalism_score,
                "fact_check_status": a.fact_check_status.value if hasattr(a.fact_check_status, "value") else str(a.fact_check_status),
                "key_claims": a.key_claims,
                "corroborating_sources": a.corroborating_sources,
                "bias_spectrum": a.bias_spectrum,
            })
        if modified:
            await db.commit()

        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "data", "news.json"))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"🚀 Successfully written {len(dataset)} verified live news articles to {output_path}")

        # Update sitemap.xml for Google Search Console & Google News indexing
        update_sitemap_xml(dataset[:50])

        return len(dataset)


def update_sitemap_xml(top_articles: list):
    """Generate dynamic XML sitemap with Google News schema for GSC."""
    sitemap_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "sitemap.xml"))
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    static_urls = [
        ("https://samachar-news-2026.web.app/", "always", "1.0"),
        ("https://samachar-news-2026.web.app/home.html", "always", "0.95"),
        ("https://samachar-news-2026.web.app/latest.html", "hourly", "0.90"),
        ("https://samachar-news-2026.web.app/trending.html", "hourly", "0.85"),
        ("https://samachar-news-2026.web.app/factcheck.html", "daily", "0.85"),
        ("https://samachar-news-2026.web.app/latest.html?cat=world", "hourly", "0.80"),
        ("https://samachar-news-2026.web.app/latest.html?cat=technology", "hourly", "0.80"),
        ("https://samachar-news-2026.web.app/latest.html?cat=india", "hourly", "0.80"),
        ("https://samachar-news-2026.web.app/latest.html?cat=business", "hourly", "0.80"),
        ("https://samachar-news-2026.web.app/latest.html?cat=science", "hourly", "0.80"),
        ("https://samachar-news-2026.web.app/latest.html?cat=health", "hourly", "0.80"),
        ("https://samachar-news-2026.web.app/latest.html?cat=sports", "hourly", "0.75"),
        ("https://samachar-news-2026.web.app/latest.html?cat=entertainment", "hourly", "0.75"),
        ("https://samachar-news-2026.web.app/about.html", "monthly", "0.60"),
        ("https://samachar-news-2026.web.app/privacy.html", "monthly", "0.50"),
        ("https://samachar-news-2026.web.app/terms.html", "monthly", "0.50"),
    ]

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
        '',
        '  <!-- Core Static & Pillar Pages -->',
    ]

    for loc, freq, priority in static_urls:
        xml_lines.extend([
            '  <url>',
            f'    <loc>{loc}</loc>',
            f'    <lastmod>{today_str}</lastmod>',
            f'    <changefreq>{freq}</changefreq>',
            f'    <priority>{priority}</priority>',
            '  </url>',
        ])

    if top_articles:
        xml_lines.append('')
        xml_lines.append('  <!-- Dynamic Articles with Google News Schemas -->')
        import html
        for art in top_articles:
            art_id = art.get("id")
            title = html.escape(art.get("title") or "News Article")
            pub_date = art.get("published_at") or today_str
            # Shorten pub date to ISO format if needed
            if len(pub_date) > 10:
                pub_date_tag = pub_date[:19] + "Z" if not pub_date.endswith("Z") else pub_date
            else:
                pub_date_tag = f"{pub_date}T00:00:00Z"
            xml_lines.extend([
                '  <url>',
                f'    <loc>https://samachar-news-2026.web.app/article.html?id={art_id}</loc>',
                f'    <lastmod>{today_str}</lastmod>',
                '    <changefreq>daily</changefreq>',
                '    <priority>0.75</priority>',
                '    <news:news>',
                '      <news:publication>',
                '        <news:name>Samachar Truth First</news:name>',
                '        <news:language>en</news:language>',
                '      </news:publication>',
                f'      <news:publication_date>{pub_date_tag}</news:publication_date>',
                f'      <news:title>{title}</news:title>',
                '    </news:news>',
                '  </url>',
            ])

    xml_lines.append('')
    xml_lines.append('</urlset>')

    try:
        with open(sitemap_path, "w", encoding="utf-8") as sf:
            sf.write("\n".join(xml_lines) + "\n")
        logger.info(f"🗺️  Updated XML Sitemap with {len(top_articles)} dynamic stories at {sitemap_path}")
    except Exception as e:
        logger.error(f"Failed to write sitemap.xml: {e}")



async def run_continuous_loop(interval_minutes: int = 15):
    """Run continuously 24x7 in background."""
    logger.info(f"🔄 Starting 24x7 News Daemon (Interval: Every {interval_minutes} minutes)")
    while True:
        try:
            await update_live_news_dataset()
        except Exception as e:
            logger.error(f"❌ Error during scheduled news update: {e}", exc_info=True)
        await asyncio.sleep(interval_minutes * 60)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        asyncio.run(run_continuous_loop(15))
    else:
        asyncio.run(update_live_news_dataset())
