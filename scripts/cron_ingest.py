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
    """Generate dynamic XML sitemaps and RSS feed strictly adhering to Google Search Console & Google News guidelines."""
    import html
    from datetime import datetime, timezone, timedelta

    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    today_dt = datetime.now(timezone.utc)
    today_str = today_dt.strftime("%Y-%m-%d")
    cutoff_48h = today_dt - timedelta(hours=48)

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

    # -------------------------------------------------------------
    # 1. Generate Master sitemap.xml
    # -------------------------------------------------------------
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, freq, priority in static_urls:
        sitemap_lines.extend([
            '  <url>',
            f'    <loc>{loc}</loc>',
            f'    <lastmod>{today_str}</lastmod>',
            f'    <changefreq>{freq}</changefreq>',
            f'    <priority>{priority}</priority>',
            '  </url>',
        ])
    for art in top_articles:
        art_id = art.get("id")
        pub_date = (art.get("published_at") or today_str)[:10]
        sitemap_lines.extend([
            '  <url>',
            f'    <loc>https://samachar-news-2026.web.app/article.html?id={art_id}</loc>',
            f'    <lastmod>{pub_date}</lastmod>',
            '    <changefreq>daily</changefreq>',
            '    <priority>0.75</priority>',
            '  </url>',
        ])
    sitemap_lines.append('</urlset>')

    sitemap_path = os.path.join(frontend_dir, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap_lines) + "\n")
    logger.info(f"🗺️  Generated Master XML Sitemap at {sitemap_path}")

    # -------------------------------------------------------------
    # 2. Generate Google News Dedicated sitemap-news.xml (Last 48 Hours)
    # -------------------------------------------------------------
    news_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]
    recent_count = 0
    for art in top_articles:
        raw_pub = art.get("published_at")
        pub_dt = today_dt
        if raw_pub:
            try:
                pub_dt = datetime.fromisoformat(raw_pub.replace("Z", "+00:00"))
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            except Exception:
                pub_dt = today_dt

        # Strict Google News rule: Only include stories from the last 48 hours
        if pub_dt >= cutoff_48h:
            recent_count += 1
            art_id = art.get("id")
            title = html.escape(art.get("title") or "News Article")
            pub_date_tag = pub_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            news_lines.extend([
                '  <url>',
                f'    <loc>https://samachar-news-2026.web.app/article.html?id={art_id}</loc>',
                '    <news:news>',
                '      <news:publication>',
                '        <news:name>Samachar News Intelligence</news:name>',
                '        <news:language>en</news:language>',
                '      </news:publication>',
                f'      <news:publication_date>{pub_date_tag}</news:publication_date>',
                f'      <news:title>{title}</news:title>',
                '    </news:news>',
                '  </url>',
            ])

    news_lines.append('</urlset>')
    news_sitemap_path = os.path.join(frontend_dir, "sitemap-news.xml")
    with open(news_sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(news_lines) + "\n")
    logger.info(f"📰 Generated Google News Sitemap ({recent_count} stories within 48h) at {news_sitemap_path}")

    # -------------------------------------------------------------
    # 3. Generate Valid RSS 2.0 Feed for Google News Publisher Center
    # -------------------------------------------------------------
    rss_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        '    <title>Samachar — Truth-First Real-Time News Wire</title>',
        '    <link>https://samachar-news-2026.web.app/</link>',
        '    <description>Autonomous real-time news intelligence and fact verification network.</description>',
        '    <language>en</language>',
        '    <atom:link href="https://samachar-news-2026.web.app/rss.xml" rel="self" type="application/rss+xml"/>',
        f'    <lastBuildDate>{today_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>',
    ]
    for art in top_articles[:30]:
        art_id = art.get("id")
        title = html.escape(art.get("title") or "")
        summary = html.escape(art.get("summary") or "")
        link = f"https://samachar-news-2026.web.app/article.html?id={art_id}"
        rss_lines.extend([
            '    <item>',
            f'      <title>{title}</title>',
            f'      <link>{link}</link>',
            f'      <guid isPermaLink="true">{link}</guid>',
            f'      <description>{summary}</description>',
            f'      <pubDate>{today_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")}</pubDate>',
            '    </item>',
        ])
    rss_lines.extend([
        '  </channel>',
        '</rss>',
    ])
    rss_path = os.path.join(frontend_dir, "rss.xml")
    with open(rss_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rss_lines) + "\n")
    logger.info(f"📡 Generated Google Publisher RSS Feed at {rss_path}")



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
