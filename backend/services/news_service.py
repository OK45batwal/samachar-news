import asyncio
import logging
import re
import random
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

logger = logging.getLogger("samachar.news_service")

FEEDS_REGISTRY = [
    # World News
    {"name": "BBC World", "feed": "https://feeds.bbci.co.uk/news/world/rss.xml", "cat": "world", "country": "UK", "rel": 96},
    {"name": "Reuters World", "feed": "https://news.google.com/rss/search?q=source:Reuters+when:2d&hl=en-US&gl=US&ceid=US:en", "cat": "world", "country": "US", "rel": 98},
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
    {"name": "STAT News", "feed": "https://www.statnews.com/feed/", "cat": "health", "country": "US", "rel": 95},

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


TOPIC_IMAGE_POOLS: Dict[str, List[str]] = {
    "oil_energy": [
        "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1509391365360-2e959784a276?auto=format&fit=crop&w=1200&q=80",
    ],
    "politics_diplomacy": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1577495508048-b635879837f1?auto=format&fit=crop&w=1200&q=80",
    ],
    "crime_justice": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1505664194779-8beaceb93744?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1453873531674-2151101a6648?auto=format&fit=crop&w=1200&q=80",
    ],
    "technology": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1677442136019-21780efad99a?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",
    ],
    "business": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80",
    ],
    "science": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1507668077129-56e32842fceb?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1200&q=80",
    ],
    "health": [
        "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=1200&q=80",
    ],
    "sports": [
        "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=1200&q=80",
    ],
    "india": [
        "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1532375810709-75b1da00537c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=1200&q=80",
    ],
    "entertainment": [
        "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1200&q=80",
    ],
    "world": [
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=1200&q=80",
    ],
}


def pick_topic_fallback_image(title: str, summary: str = "", category_slug: str = "world") -> str:
    """Deterministically select a topic-relevant high-res editorial image based on article keywords."""
    text = f"{title} {summary}".lower()

    target_pool = None
    if any(k in text for k in ("oil", "crude", "petroleum", "pipeline", "gas", "fumes", "fuel", "refinery")):
        target_pool = TOPIC_IMAGE_POOLS["oil_energy"]
    elif any(k in text for k in ("election", "parliament", "vote", "voter", "far right", "afd", "coalition", "politics", "minister", "diplomat", "treaty", "summit", "senate", "congress")):
        target_pool = TOPIC_IMAGE_POOLS["politics_diplomacy"]
    elif any(k in text for k in ("court", "police", "investigat", "thief", "thieves", "arrest", "crime", "trial", "judge", "illegal", "prosecut")):
        target_pool = TOPIC_IMAGE_POOLS["crime_justice"]
    elif any(k in text for k in ("space", "nasa", "planet", "astronomy", "physics", "telescope", "quantum", "lab", "dna")):
        target_pool = TOPIC_IMAGE_POOLS["science"]
    elif any(k in text for k in ("ai", "artificial intelligence", "chip", "semiconductor", "cyber", "software", "robot", "nvidia", "apple", "google", "meta")):
        target_pool = TOPIC_IMAGE_POOLS["technology"]
    elif any(k in text for k in ("market", "stock", "inflation", "economy", "bank", "gdp", "trade", "fed", "tariff", "invest")):
        target_pool = TOPIC_IMAGE_POOLS["business"]
    elif any(k in text for k in ("health", "cancer", "hospital", "virus", "vaccine", "disease", "medical", "doctor", "clinical")):
        target_pool = TOPIC_IMAGE_POOLS["health"]
    elif any(k in text for k in ("cricket", "football", "soccer", "olympic", "fifa", "tennis", "match", "championship", "tournament")):
        target_pool = TOPIC_IMAGE_POOLS["sports"]
    elif any(k in text for k in ("india", "delhi", "mumbai", "modi", "bengaluru", "isro")):
        target_pool = TOPIC_IMAGE_POOLS["india"]
    elif any(k in text for k in ("movie", "film", "cinema", "hollywood", "bollywood", "music", "oscar", "concert", "actor")):
        target_pool = TOPIC_IMAGE_POOLS["entertainment"]

    if not target_pool:
        cat = (category_slug or "world").lower().strip()
        target_pool = TOPIC_IMAGE_POOLS.get(cat, TOPIC_IMAGE_POOLS["world"])

    # Deterministic selection based on title character codes
    title_hash = sum(ord(c) for c in (title or "news"))
    return target_pool[title_hash % len(target_pool)]


def _extract_image_url(entry: Any) -> Optional[str]:
    # 1. Media enclosure
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if isinstance(enc, dict):
                href = enc.get('href', '')
                enc_type = enc.get('type', '')
                if enc_type.startswith('image/') or any(href.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.avif')):
                    return href

    # 2. Links array (common in Atom/RSS feeds)
    if hasattr(entry, 'links') and entry.links:
        for link in entry.links:
            if isinstance(link, dict):
                href = link.get('href', '')
                ltype = link.get('type', '')
                rel = link.get('rel', '')
                if ltype.startswith('image/') or rel in ('enclosure', 'image') or any(href.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp', '.avif')):
                    return href

    # 3. Media content
    if hasattr(entry, 'media_content') and entry.media_content:
        for m in entry.media_content:
            if isinstance(m, dict) and m.get('url'):
                return m.get('url')

    # 4. Media thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for t in entry.media_thumbnail:
            if isinstance(t, dict) and t.get('url'):
                return t.get('url')

    # 5. Extract from summary / description / content HTML img tags
    candidates = [
        entry.get('summary', ''),
        entry.get('description', ''),
    ]
    if hasattr(entry, 'content') and entry.content:
        for c in entry.content:
            if isinstance(c, dict):
                candidates.append(c.get('value', ''))
            else:
                candidates.append(str(c))

    for html_chunk in candidates:
        if html_chunk:
            img_match = re.search(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', html_chunk, re.IGNORECASE)
            if img_match:
                url = img_match.group(1)
                # Filter out tracking pixels / tiny icons
                if not any(bad in url.lower() for bad in ('1x1', 'pixel', 'tracker', 'spacer')):
                    return url
    return None


async def ingest_single_feed(feed_info: Dict[str, Any], client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    articles = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = await client.get(
            feed_info["feed"],
            headers=headers,
            timeout=10.0,
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
            if not image_url:
                image_url = pick_topic_fallback_image(title, summary, feed_info["cat"])
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
    except Exception as e:
        logger.warning("Feed ingestion error for %s (%s): %s", feed_info.get("name"), feed_info.get("feed"), e)
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

        seen_urls = set()
        for item in all_fetched:
            if not item.get("source_url") or item["source_url"] in seen_urls:
                continue
            seen_urls.add(item["source_url"])

            src_name = item.get("source_name", "News Wire")
            if src_name not in sources:
                new_src = Source(
                    name=src_name,
                    country=item.get("country", "Global"),
                    reliability_score=90,
                    bias_rating="center"
                )
                db.add(new_src)
                await db.flush()
                sources[src_name] = new_src.id

            # Check for duplicate URL in DB
            existing = await db.execute(select(Article).where(Article.source_url == item["source_url"]))
            if existing.scalar_one_or_none():
                continue

            # Run Fact-Checking Engine
            fact_metrics = evaluate_article_credibility(
                title=item["title"],
                summary=item["summary"],
                content=item["content"],
                source_name=src_name,
                corroborating_count=2,
            )

            # Generate unique slug
            base_slug = re.sub(r'[^a-zA-Z0-9]+', '-', item["title"].lower()).strip('-')[:120]
            unique_slug = f"{base_slug}-{int(datetime.now().timestamp())}-{random.randint(100, 999)}"

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
                corroborating_sources=[src_name] if src_name else [],
                bias_spectrum=fact_metrics["bias_spectrum"],
                category_id=categories.get(item["category_slug"], list(categories.values())[0] if categories else None),
                source_id=sources.get(src_name),
                published_at=item["published_at"],
            )
            try:
                db.add(article)
                await db.commit()
                created_count += 1
                if fact_metrics["credibility_score"] >= 80:
                    verified_count += 1
                try:
                    from ..websocket.ws import manager
                    status_str = article.fact_check_status.value if hasattr(article.fact_check_status, 'value') else str(article.fact_check_status)
                    await manager.broadcast({
                        "type": "new_article",
                        "article": {
                            "id": article.id,
                            "title": article.title,
                            "slug": article.slug,
                            "summary": article.summary,
                            "credibility_score": article.credibility_score,
                            "fact_check_status": status_str,
                            "source": src_name,
                            "image_url": article.image_url,
                            "published_at": article.published_at.isoformat() if article.published_at else None,
                        }
                    })
                except Exception as ws_err:
                    logger.debug("Live websocket broadcast skipped: %s", ws_err)
            except Exception as e:
                logger.warning("Failed to persist article '%s': %s", item.get("title", "")[:50], e)
                await db.rollback()

    return {
        "fetched": len(all_fetched),
        "created": created_count,
        "verified": verified_count,
    }
