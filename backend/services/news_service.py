import asyncio
import time
from datetime import datetime
from typing import Optional

import feedparser
import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import async_session
from ..models.models import Article, ArticleStatus, Category, Source
from ..utils.utils import slugify
from .feed_parser import extract_image_fallback

logger = structlog.get_logger(__name__)

FEED_CONFIG = {
    # ── World News ──
    "bbc_world":         {"name": "BBC World",         "category": "world", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "country": "UK", "language": "en"},
    "guardian_world":    {"name": "The Guardian",       "category": "world", "url": "https://www.theguardian.com/world/rss", "country": "UK", "language": "en"},
    "npr":               {"name": "NPR News",           "category": "world", "url": "https://feeds.npr.org/1001/rss.xml", "country": "US", "language": "en"},
    "pbs":               {"name": "PBS NewsHour",       "category": "world", "url": "https://www.pbs.org/newshour/feeds/rss/headlines", "country": "US", "language": "en"},
    "abc_news":          {"name": "ABC News",           "category": "world", "url": "https://feeds.abcnews.com/abcnews/topstories", "country": "US", "language": "en"},
    "cbs_news":          {"name": "CBS News",           "category": "world", "url": "https://www.cbsnews.com/latest/rss/main", "country": "US", "language": "en"},
    "nbc_news":          {"name": "NBC News",           "category": "world", "url": "https://feeds.nbcnews.com/nbcnews/public/news", "country": "US", "language": "en"},
    "france24":          {"name": "France 24",          "category": "world", "url": "https://www.france24.com/en/rss", "country": "France", "language": "en"},
    "euronews":          {"name": "Euronews",           "category": "world", "url": "https://www.euronews.com/rss?format=xml", "country": "EU", "language": "en"},
    "dw":                {"name": "DW News",            "category": "world", "url": "https://rss.dw.com/xml/rss-en-all", "country": "Germany", "language": "en"},
    "axios":             {"name": "Axios",              "category": "world", "url": "https://api.axios.com/feed/", "country": "US", "language": "en"},
    "the_hill":          {"name": "The Hill",           "category": "politics", "url": "https://thehill.com/news/feed", "country": "US", "language": "en"},
    "politico":          {"name": "Politico",           "category": "politics", "url": "https://rss.politico.com/politics-news.xml", "country": "US", "language": "en"},

    # ── Technology ──
    "techcrunch":        {"name": "TechCrunch",         "category": "technology", "url": "https://techcrunch.com/feed/", "country": "US", "language": "en"},
    "the_verge":         {"name": "The Verge",          "category": "technology", "url": "https://www.theverge.com/rss/index.xml", "country": "US", "language": "en"},
    "ars_technica":      {"name": "Ars Technica",       "category": "technology", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "country": "US", "language": "en"},
    "mit_tech":          {"name": "MIT Tech Review",    "category": "technology", "url": "https://www.technologyreview.com/feed/", "country": "US", "language": "en"},
    "zdnet":             {"name": "ZDNet",              "category": "technology", "url": "https://www.zdnet.com/news/rss.xml", "country": "US", "language": "en"},
    "engadget":          {"name": "Engadget",           "category": "technology", "url": "https://www.engadget.com/rss.xml", "country": "US", "language": "en"},
    "venturebeat":       {"name": "VentureBeat",        "category": "technology", "url": "https://venturebeat.com/feed/", "country": "US", "language": "en"},
    "fast_company":      {"name": "Fast Company",       "category": "technology", "url": "https://feeds.feedburner.com/fastcompany/headlines", "country": "US", "language": "en"},
    "hacker_news":       {"name": "Hacker News",        "category": "technology", "url": "https://hnrss.org/frontpage", "country": "US", "language": "en"},
    "wired":             {"name": "Wired",              "category": "technology", "url": "https://www.wired.com/feed/rss", "country": "US", "language": "en"},
    "mit_research":      {"name": "MIT Research",       "category": "science", "url": "https://news.mit.edu/rss/research", "country": "US", "language": "en"},
    "tech_in_asia":      {"name": "Tech in Asia",       "category": "technology", "url": "https://www.techinasia.com/feed", "country": "Singapore", "language": "en"},

    # ── Business & Finance ──
    "cnbc":              {"name": "CNBC",               "category": "business", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "country": "US", "language": "en"},
    "yahoo_finance":     {"name": "Yahoo Finance",      "category": "business", "url": "https://finance.yahoo.com/rss/topstories", "country": "US", "language": "en"},
    "marketwatch":       {"name": "MarketWatch",        "category": "business", "url": "https://feeds.marketwatch.com/marketwatch/topstories/", "country": "US", "language": "en"},
    "coindesk":          {"name": "CoinDesk",           "category": "business", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "country": "US", "language": "en"},
    "cointelegraph":     {"name": "Cointelegraph",      "category": "business", "url": "https://cointelegraph.com/rss", "country": "US", "language": "en"},
    "federal_reserve":   {"name": "Federal Reserve",    "category": "business", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "country": "US", "language": "en"},

    # ── Sports ──
    "bbc_sport":         {"name": "BBC Sport",          "category": "sports", "url": "https://feeds.bbci.co.uk/sport/rss.xml", "country": "UK", "language": "en"},
    "espn":              {"name": "ESPN",               "category": "sports", "url": "https://www.espn.com/espn/rss/news", "country": "US", "language": "en"},
    "sky_sports":        {"name": "Sky Sports",         "category": "sports", "url": "https://www.skysports.com/rss/12040", "country": "UK", "language": "en"},

    # ── Science ──
    "nature":            {"name": "Nature",             "category": "science", "url": "https://www.nature.com/feed/", "country": "UK", "language": "en"},
    "new_scientist":     {"name": "New Scientist",      "category": "science", "url": "https://www.newscientist.com/feed/home", "country": "UK", "language": "en"},
    "science_daily":     {"name": "Science Daily",      "category": "science", "url": "https://www.sciencedaily.com/rss/all.xml", "country": "US", "language": "en"},
    "phys_org":          {"name": "Phys.org",           "category": "science", "url": "https://phys.org/rss-feed/", "country": "US", "language": "en"},
    "space_com":         {"name": "Space.com",          "category": "science", "url": "https://www.space.com/feeds/all", "country": "US", "language": "en"},
    "arxiv_ai":          {"name": "ArXiv AI",           "category": "science", "url": "https://export.arxiv.org/rss/cs.AI", "country": "US", "language": "en"},

    # ── Health ──
    "who":               {"name": "WHO",                "category": "health", "url": "https://www.who.int/rss-feeds/news-english.xml", "country": "Switzerland", "language": "en"},
    "cdc":               {"name": "CDC",                "category": "health", "url": "https://tools.cdc.gov/api/v2/resources/media/404501.rss", "country": "US", "language": "en"},
    "webmd":             {"name": "WebMD",              "category": "health", "url": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC", "country": "US", "language": "en"},

    # ── Entertainment ──
    "variety":           {"name": "Variety",            "category": "entertainment", "url": "https://variety.com/feed/", "country": "US", "language": "en"},
    "hollywood_reporter": {"name": "Hollywood Reporter", "category": "entertainment", "url": "https://www.hollywoodreporter.com/feed/", "country": "US", "language": "en"},
    "billboard":         {"name": "Billboard",          "category": "entertainment", "url": "https://www.billboard.com/feed/", "country": "US", "language": "en"},
    "rolling_stone":     {"name": "Rolling Stone",      "category": "entertainment", "url": "https://www.rollingstone.com/feed/", "country": "US", "language": "en"},
    "pitchfork":         {"name": "Pitchfork",          "category": "entertainment", "url": "https://pitchfork.com/feed/feed-news/rss", "country": "US", "language": "en"},

    # ── India / South Asia ──
    "bbc_hindi":         {"name": "BBC Hindi",          "category": "world", "url": "https://www.bbc.com/hindi/index.xml", "country": "India", "language": "hi"},
    "ndtv":              {"name": "NDTV",               "category": "world", "url": "https://feeds.feedburner.com/ndtvnews-latest", "country": "India", "language": "en"},
    "the_hindu":         {"name": "The Hindu",          "category": "world", "url": "https://www.thehindu.com/news/feeder/default.rss", "country": "India", "language": "en"},
    "indian_exp":        {"name": "Indian Express",     "category": "world", "url": "https://indianexpress.com/feed/", "country": "India", "language": "en"},
    "times_of_india":    {"name": "Times of India",     "category": "world", "url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", "country": "India", "language": "en"},
    "hindu_business":    {"name": "Hindu BusinessLine", "category": "business", "url": "https://www.thehindubusinessline.com/feeder/default.rss", "country": "India", "language": "en"},
    "yourstory":         {"name": "YourStory",          "category": "technology", "url": "https://yourstory.com/feed", "country": "India", "language": "en"},
    "inc42":             {"name": "Inc42",              "category": "technology", "url": "https://inc42.com/feed/", "country": "India", "language": "en"},

    # ── Regional / Language (EU) ──
    "le_monde":          {"name": "Le Monde",           "category": "world", "url": "https://www.lemonde.fr/en/rss/une.xml", "country": "France", "language": "en"},
    "el_pais":           {"name": "El País",            "category": "world", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "country": "Spain", "language": "es"},
    "tagesschau":        {"name": "Tagesschau",         "category": "world", "url": "https://www.tagesschau.de/xml/rss2/", "country": "Germany", "language": "de"},
    "spiegel":           {"name": "Der Spiegel",        "category": "world", "url": "https://www.spiegel.de/schlagzeilen/tops/index.rss", "country": "Germany", "language": "de"},
    "ansa":              {"name": "ANSA",               "category": "world", "url": "https://www.ansa.it/sito/notizie/topnews/topnews_rss.xml", "country": "Italy", "language": "it"},
    "nos":               {"name": "NOS Nieuws",         "category": "world", "url": "https://feeds.nos.nl/nosnieuwsalgemeen", "country": "Netherlands", "language": "nl"},
}

async def _get_category(db: AsyncSession, slug: str) -> Optional[Category]:
    result = await db.execute(select(Category).where(Category.slug == slug))
    return result.scalar_one_or_none()

async def _get_source(db: AsyncSession, key: str, config: dict) -> Optional[Source]:
    result = await db.execute(select(Source).where(Source.name == config["name"]))
    source = result.scalar_one_or_none()
    if not source:
        source = Source(
            name=config["name"],
            feed_url=config["url"],
            country=config.get("country", ""),
            language=config.get("language", "en"),
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
    return source

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

_extract_image = extract_image_fallback


def _parse_feed(feed_url: str):
    return feedparser.parse(feed_url)

async def _ingest_feed(db, key, cfg):
    """Parse and store a single feed. Returns article count."""
    try:
        feed = await asyncio.wait_for(
            asyncio.to_thread(_parse_feed, cfg["url"]), timeout=15
        )
    except Exception as e:
        logger.error("Failed to parse feed %s: %s", cfg["url"], e)
        return 0

    if feed.bozo and not feed.entries:
        logger.warning("Feed %s returned no entries (bozo=%s)", cfg["url"], feed.bozo)
        return 0

    source = await _get_source(db, key, cfg)
    if not source:
        return 0

    category = await _get_category(db, cfg["category"])
    if not category:
        logger.warning("Category '%s' not found for feed %s", cfg["category"], key)
        return 0

    count = 0
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

        published = datetime.utcnow()
        if entry.get("published_parsed"):
            try:
                published = datetime(*entry.get("published_parsed")[:6])
            except Exception:
                pass

        img = _extract_image(entry)
        title_text = entry.get("title", "")
        summary_text = (entry.get("summary") or "")[:500]

        from ..ai.processor import analyze_sentiment
        sentiment = analyze_sentiment(title_text + " " + summary_text)

        article = Article(
            title=title_text,
            slug=slug,
            summary=summary_text,
            content=(entry.get("content", [{}])[0].get("value", "")
                     if entry.get("content") else summary_text),
            image_url=img,
            source_url=link,
            author=entry.get("author", ""),
            status=ArticleStatus.PUBLISHED,
            sentiment_score=sentiment,
            category_id=category.id,
            source_id=source.id,
            published_at=published,
        )
        db.add(article)
        count += 1

    return count

NEWSAPI_CATEGORY_MAP = {
    "general": "world", "world": "world", "politics": "politics",
    "technology": "technology", "business": "business",
    "sports": "sports", "science": "science", "health": "health",
    "entertainment": "entertainment",
}

_newsapi_last_fetch = 0.0
NEWSAPI_CACHE_TTL = 600  # 10 minutes

async def fetch_newsapi(db: AsyncSession):
    """Fetch articles from NewsAPI and store them. Requires NEWS_API_KEY in .env."""
    global _newsapi_last_fetch
    api_key = settings.NEWS_API_KEY
    if not api_key:
        logger.info("NEWS_API_KEY not set — skipping NewsAPI fetch")
        return 0

    # 10-min cache guard
    now = time.time()
    if now - _newsapi_last_fetch < NEWSAPI_CACHE_TTL:
        logger.info("NewsAPI fetch skipped (within 10-min cache window)")
        return 0

    total = 0
    categories = ["general", "world", "technology", "business", "sports", "science", "health", "entertainment"]

    async with httpx.AsyncClient(timeout=15) as client:
        for cat in categories:
            try:
                resp = await client.get(
                    "https://newsapi.org/v2/top-headlines",
                    params={"category": cat, "pageSize": 12, "apiKey": api_key, "language": "en"},
                )
                if resp.status_code == 429:
                    logger.warning("NewsAPI rate limited — stopping")
                    break
                if resp.status_code != 200:
                    logger.warning("NewsAPI returned %d for %s", resp.status_code, cat)
                    continue

                data = resp.json()
                articles = data.get("articles", [])
                if not articles:
                    continue

                local_cat = NEWSAPI_CATEGORY_MAP.get(cat, "world")
                category = await _get_category(db, local_cat)
                if not category:
                    continue

                # Use first article's source as our source entry
                source_name = f"NewsAPI {cat}"
                source = await _get_source_from_name(db, source_name, cat)

                for item in articles:
                    url = item.get("url", "")
                    title = item.get("title", "")
                    if not url or not title:
                        continue

                    existing = await db.execute(select(Article).where(Article.source_url == url))
                    if existing.scalar_one_or_none():
                        continue

                    slug_base = slugify(title)[:200]
                    slug = slug_base
                    counter = 1
                    while True:
                        slug_check = await db.execute(select(Article).where(Article.slug == slug))
                        if not slug_check.scalar_one_or_none():
                            break
                        slug = f"{slug_base[:190]}-{counter}"
                        counter += 1

                    published = datetime.utcnow()
                    raw_date = item.get("publishedAt", "")
                    if raw_date:
                        try:
                            published = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).replace(tzinfo=None)
                        except Exception:
                            pass

                    img = item.get("urlToImage", "") or ""
                    if img and not img.startswith("http"):
                        img = ""

                    article = Article(
                        title=title,
                        slug=slug,
                        summary=(item.get("description") or "")[:500],
                        content=item.get("content") or item.get("description") or title,
                        image_url=img,
                        source_url=url,
                        author=item.get("author") or "",
                        status=ArticleStatus.PUBLISHED,
                        category_id=category.id,
                        source_id=source.id,
                        published_at=published,
                    )
                    db.add(article)
                    total += 1

            except Exception as e:
                logger.warning("NewsAPI fetch failed for %s: %s", cat, e)

    if total:
        await db.commit()
        _newsapi_last_fetch = now
        logger.info("NewsAPI: %d new articles stored", total)
    return total


async def _get_source_from_name(db: AsyncSession, name: str, category_slug: str) -> Optional[Source]:
    """Get or create a source by name (used by NewsAPI)."""
    result = await db.execute(select(Source).where(Source.name == name))
    source = result.scalar_one_or_none()
    if not source:
        source = Source(
            name=name,
            feed_url="",
            country="US",
            language="en",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
    return source


async def ingest_feeds():
    async with async_session() as db:
        total = 0
        succeeded = 0
        for key, cfg in FEED_CONFIG.items():
            try:
                count = await _ingest_feed(db, key, cfg)
                if count:
                    total += count
                    succeeded += 1
            except Exception as e:
                logger.warning("Feed %s failed: %s", key, e)

        await db.commit()
        logger.info("Feed ingestion: %d new articles from %d/%d sources", total, succeeded, len(FEED_CONFIG))

        try:
            await fetch_newsapi(db)
        except Exception as e:
            logger.error("NewsAPI fetch error: %s", e)
