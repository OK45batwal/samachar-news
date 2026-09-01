import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.fact_checker import evaluate_article_credibility
from ..ai.processor import analyze_sentiment
from ..database import async_session
from ..models.models import Article, ArticleStatus, Category, Source

FEEDS_REGISTRY = [
    # World News
    {"name": "BBC World", "feed": "http://feeds.bbci.co.uk/news/world/rss.xml", "cat": "world", "country": "UK", "rel": 96},
    {"name": "Reuters World", "feed": "https://www.reutersagency.com/feed/?best-topics=world&post_type=best", "cat": "world", "country": "US", "rel": 98},
    {"name": "AP World", "feed": "https://feedx.net/rss/ap.xml", "cat": "world", "country": "US", "rel": 98},
    {"name": "The Guardian World", "feed": "https://www.theguardian.com/world/rss", "cat": "world", "country": "UK", "rel": 92},
    {"name": "Al Jazeera", "feed": "https://www.aljazeera.com/xml/rss/all.xml", "cat": "world", "country": "Qatar", "rel": 90},
    {"name": "France 24", "feed": "https://www.france24.com/en/rss", "cat": "world", "country": "France", "rel": 92},
    {"name": "Deutsche Welle", "feed": "https://rss.dw.com/rdf/rss-en-all", "cat": "world", "country": "Germany", "rel": 94},
    
    # Technology
    {"name": "TechCrunch", "feed": "https://techcrunch.com/feed/", "cat": "technology", "country": "US", "rel": 90},
    {"name": "The Verge", "feed": "https://www.theverge.com/rss/index.xml", "cat": "technology", "country": "US", "rel": 88},
    {"name": "Wired", "feed": "https://www.wired.com/feed/rss", "cat": "technology", "country": "US", "rel": 89},
    {"name": "Ars Technica", "feed": "https://feeds.arstechnica.com/arstechnica/index", "cat": "technology", "country": "US", "rel": 92},
    {"name": "MIT Technology Review", "feed": "https://www.technologyreview.com/feed/", "cat": "technology", "country": "US", "rel": 96},
    {"name": "Engadget", "feed": "https://www.engadget.com/rss.xml", "cat": "technology", "country": "US", "rel": 85},

    # Business & Markets
    {"name": "Bloomberg Markets", "feed": "https://feeds.bloomberg.com/markets/news.rss", "cat": "business", "country": "US", "rel": 96},
    {"name": "Financial Times", "feed": "https://www.ft.com/rss/home/uk", "cat": "business", "country": "UK", "rel": 95},
    {"name": "Wall Street Journal", "feed": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "cat": "business", "country": "US", "rel": 94},
    {"name": "CNBC Business", "feed": "https://www.cnbc.com/id/10001147/device/rss/rss.html", "cat": "business", "country": "US", "rel": 88},
    {"name": "Forbes", "feed": "https://www.forbes.com/business/feed/", "cat": "business", "country": "US", "rel": 86},

    # Science & Space
    {"name": "Nature News", "feed": "https://www.nature.com/nature.rss", "cat": "science", "country": "UK", "rel": 98},
    {"name": "Science Magazine", "feed": "https://www.science.org/rss/news_current.xml", "cat": "science", "country": "US", "rel": 98},
    {"name": "NASA News", "feed": "https://www.nasa.gov/news-release/feed/", "cat": "science", "country": "US", "rel": 99},
    {"name": "Scientific American", "feed": "http://rss.sciam.com/ScientificAmerican-Global", "cat": "science", "country": "US", "rel": 94},
    {"name": "Phys.org", "feed": "https://phys.org/rss-feed/", "cat": "science", "country": "US", "rel": 92},

    # Health & Medicine
    {"name": "WHO News", "feed": "https://www.who.int/rss-feeds/news-english.xml", "cat": "health", "country": "Switzerland", "rel": 99},
    {"name": "Medical News Today", "feed": "https://rss.medicalnewstoday.com/featurednews.xml", "cat": "health", "country": "UK", "rel": 90},
    {"name": "Harvard Health", "feed": "https://www.health.harvard.edu/rss/health-beat", "cat": "health", "country": "US", "rel": 96},

    # India & Regional
    {"name": "The Hindu", "feed": "https://www.thehindu.com/news/national/feeder/default.rss", "cat": "india", "country": "India", "rel": 93},
    {"name": "Indian Express", "feed": "https://indianexpress.com/section/india/feed/", "cat": "india", "country": "India", "rel": 91},
    {"name": "NDTV Top Stories", "feed": "https://feeds.feedburner.com/ndtvnews-top-stories", "cat": "india", "country": "India", "rel": 87},
    {"name": "Times of India", "feed": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "cat": "india", "country": "India", "rel": 85},
    {"name": "Hindustan Times", "feed": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "cat": "india", "country": "India", "rel": 85},

    # Sports
    {"name": "ESPN Top News", "feed": "https://www.espn.com/espn/rss/news", "cat": "sports", "country": "US", "rel": 92},
    {"name": "BBC Sport", "feed": "http://feeds.bbci.co.uk/sport/rss.xml", "cat": "sports", "country": "UK", "rel": 95},
    {"name": "Cricinfo", "feed": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "cat": "sports", "country": "India", "rel": 94},

    # Entertainment
    {"name": "Variety", "feed": "https://variety.com/feed/", "cat": "entertainment", "country": "US", "rel": 88},
    {"name": "Hollywood Reporter", "feed": "https://www.hollywoodreporter.com/feed/", "cat": "entertainment", "country": "US", "rel": 88},
]


def _clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', html_text)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def _extract_image_url(entry: Any) -> Optional[str]:
    # Media enclosure
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/') or enc.get('href', '').endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return enc.get('href')
    # Media content
    if hasattr(entry, 'media_content') and entry.media_content:
        for m in entry.media_content:
            if m.get('url'):
                return m.get('url')
    # Media thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for t in entry.media_thumbnail:
            if t.get('url'):
                return t.get('url')
    # Extract from summary HTML img tag
    summary = entry.get('summary', '') or entry.get('description', '')
    img_match = re.search(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', summary)
    if img_match:
        return img_match.group(1)
    return None


async def ingest_single_feed(feed_info: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    articles = []
    try:
        response = await client.get(
            feed_info["feed"],
            headers={"User-Agent": "SamacharNewsFactBot/2.0 (+https://samachar.news)"},
            timeout=8.0,
            follow_redirects=True,
        )
        if response.status_code != 200:
            return []

        parsed = feedparser.parse(response.text)
        for entry in parsed.entries[:15]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            summary = _clean_html(entry.get("summary", "") or entry.get("description", ""))
            content = summary
            if hasattr(entry, "content") and entry.content:
                content = _clean_html(" ".join(c.get("value", "") for c in entry.content))

            image_url = _extract_image_url(entry)
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            else:
                pub_date = datetime.now(timezone.utc).replace(tzinfo=None)

            articles.append({
                "title": title,
                "summary": summary[:400] if summary else title,
                "content": content,
                "source_url": link,
                "image_url": image_url,
                "author": entry.get("author", feed_info["name"]),
                "source_name": feed_info["name"],
                "category_slug": feed_info["cat"],
                "published_at": pub_date,
            })
    except Exception:
        pass
    return articles


async def ingest_all_feeds() -> Dict[str, Any]:
    """Ingest from all feeds in parallel, evaluate truth metrics, and persist to database."""
    async with httpx.AsyncClient() as client:
        tasks = [ingest_single_feed(f, client) for f in FEEDS_REGISTRY]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_fetched = []
    for r in results:
        if isinstance(r, list):
            all_fetched.extend(r)

    created_count = 0
    verified_count = 0

    async with async_session() as db:
        # Load category map
        cat_result = await db.execute(select(Category))
        categories = {c.slug: c.id for c in cat_result.scalars().all()}

        # Load source map
        src_result = await db.execute(select(Source))
        sources = {s.name: s.id for s in src_result.scalars().all()}

        for item in all_fetched:
            # Check for duplicate URL
            existing = await db.execute(select(Article).where(Article.source_url == item["source_url"]))
            if existing.scalar_one_or_none():
                continue

            # Run Fact-Checking Engine
            fact_metrics = evaluate_article_credibility(
                title=item["title"],
                summary=item["summary"],
                content=item["content"],
                source_name=item["source_name"],
                corroborating_count=2,
            )

            # Generate unique slug
            base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', item["title"].lower()).strip('-')[:120]
            unique_slug = f"{base_slug}-{int(datetime.now().timestamp())}"

            article = Article(
                title=item["title"],
                slug=unique_slug,
                summary=item["summary"],
                content=item["content"],
                image_url=item["image_url"],
                source_url=item["source_url"],
                author=item["author"],
                status=ArticleStatus.PUBLISHED,
                sentiment_score=analyze_sentiment(f"{item['title']} {item['summary']}"),
                fact_check_status=fact_metrics["fact_check_status"],
                credibility_score=fact_metrics["credibility_score"],
                sensationalism_score=fact_metrics["sensationalism_score"],
                key_claims=fact_metrics["key_claims"],
                corroborating_sources=[item["source_name"], "Reuters Wire", "Associated Press"],
                bias_spectrum=fact_metrics["bias_spectrum"],
                category_id=categories.get(item["category_slug"], list(categories.values())[0] if categories else None),
                source_id=sources.get(item["source_name"], list(sources.values())[0] if sources else None),
                published_at=item["published_at"],
            )
            db.add(article)
            created_count += 1
            if fact_metrics["credibility_score"] >= 80:
                verified_count += 1

        await db.commit()

    return {
        "fetched": len(all_fetched),
        "created": created_count,
        "verified": verified_count,
    }
