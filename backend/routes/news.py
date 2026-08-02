import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.models import Article, ArticleStatus, Category, Source
from ..schemas import ArticleListOut, ArticleOut

router = APIRouter(prefix="/api/news", tags=["news"])

STOP_WORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','by','with',
    'from','as','is','was','are','were','be','been','being','have','has','had',
    'do','does','did','will','would','could','should','may','might','shall',
    'can','not','no','nor','its','it','this','that','these','those','all',
    'each','every','both','few','more','most','some','any','new','after',
    'over','under','up','down','out','off','about','into','through','during',
    'before','between','than','also','just','very','too','yet','so','if',
    'because','while','when','where','how','what','which','who','whom','why',
}

COUNTRY_COORDS = {
    "US": (37.0902, -95.7129), "UK": (55.3781, -3.4360), "India": (20.5937, 78.9629),
    "Germany": (51.1657, 10.4515), "France": (46.6034, 1.8883), "China": (35.8617, 104.1954),
    "Russia": (61.5240, 105.3188), "Japan": (36.2048, 138.2529), "Brazil": (-14.2350, -51.9253),
    "Canada": (56.1304, -106.3468), "Australia": (-25.2744, 133.7751), "Spain": (40.4637, -3.7492),
    "Italy": (41.8719, 12.5674), "Switzerland": (46.8182, 8.2275), "Netherlands": (52.1326, 5.2913),
    "Singapore": (1.3521, 103.8198), "EU": (50.8503, 4.3517), "South Africa": (-30.5595, 22.9375),
    "South Korea": (35.9078, 127.7669), "North Korea": (40.3399, 127.5101),
    "UAE": (23.4241, 53.8478), "Saudi Arabia": (23.8859, 45.0792),
    "Israel": (31.0461, 34.8516), "Iran": (32.4279, 53.6880),
    "Turkey": (38.9637, 35.2433), "Pakistan": (30.3753, 69.3451),
    "Bangladesh": (23.6850, 90.3563), "Nigeria": (9.0820, 8.6753),
    "Kenya": (-0.0236, 37.9062), "Egypt": (26.8206, 30.8025),
    "Argentina": (-38.4161, -63.6167), "Mexico": (23.6345, -102.5528),
    "Colombia": (4.5709, -74.2973), "Chile": (-35.6751, -71.5430),
    "Sweden": (60.1282, 18.6435), "Norway": (60.4720, 8.4689),
    "Denmark": (56.2639, 9.5018), "Finland": (61.9241, 25.7482),
    "Poland": (51.9194, 19.1451), "Ukraine": (48.3794, 31.1656),
    "New Zealand": (-40.9006, 174.8860), "Indonesia": (-0.7893, 113.9213),
    "Vietnam": (14.0583, 108.2772), "Thailand": (15.8700, 100.9925),
    "Malaysia": (4.2105, 101.9758), "Philippines": (12.8797, 121.7740),
    "Taiwan": (23.6978, 120.9605), "Hong Kong": (22.3193, 114.1694),
}

COUNTRY_ALIASES = {
    "USA": "US", "United States": "US", "America": "US", "U.S.": "US", "US-based": "US",
    "Britain": "UK", "Great Britain": "UK", "England": "UK", "United Kingdom": "UK", "UK-based": "UK",
    "South Korea": "South Korea", "North Korea": "North Korea",
    "UAE": "UAE", "United Arab Emirates": "UAE",
    "Korea": "South Korea", "DPRK": "North Korea",
    "Holland": "Netherlands", "the Netherlands": "Netherlands",
    "Czechia": "Czech Republic", "Czech Republic": "Czech Republic",
    "Burma": "Myanmar", "Myanmar": "Myanmar",
    "Ivory Coast": "Côte d'Ivoire", "Côte d'Ivoire": "Côte d'Ivoire",
    "EU": "EU", "European Union": "EU", "Europe": "EU",
    "UK-established": "UK", "US-established": "US",
    "Moscow": "Russia", "Beijing": "China", "London": "UK", "Washington": "US",
    "New Delhi": "India", "Delhi": "India",
}


def extract_countries(content: str) -> list[str]:
    if not content:
        return []
    found = set()
    upper = content.upper()
    for name in COUNTRY_COORDS:
        alias = COUNTRY_ALIASES.get(name, name)
        if alias.upper() in upper:
            found.add(name)
    for alias, target in COUNTRY_ALIASES.items():
        if alias.upper() in upper:
            found.add(target)
    found.discard("EU")
    return list(found)


@router.get("/geo")
async def get_geo_events(
    category: Optional[str] = None,
    days: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Return events grouped by country with coordinates, sentiment, and top keywords."""
    base = (
        select(Source.country, func.count(Article.id).label("cnt"),
               func.coalesce(func.avg(Article.sentiment_score), 0).label("avg_sentiment"))
        .select_from(Article)
        .join(Source, Article.source_id == Source.id)
        .where(Article.status == ArticleStatus.PUBLISHED,
               Source.country.isnot(None), Source.country != "")
    )
    if category:
        base = base.join(Category, Article.category_id == Category.id).where(Category.slug == category)
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        base = base.where(Article.published_at >= cutoff)
    base = base.group_by(Source.country).order_by(desc("cnt"))

    rows = await db.execute(base)
    country_data = {}
    keyword_buckets = {}
    for row in rows:
        name = row.country
        lat, lng = COUNTRY_COORDS.get(name)
        if lat is None:
            continue
        country_data[name] = {"cnt": row.cnt, "lat": lat, "lng": lng, "sentiment": round(float(row.avg_sentiment), 2)}
        keyword_buckets[name] = Counter()

    # Fetch titles for keyword extraction (limit per country)
    if keyword_buckets:
        title_rows = await db.execute(
            select(Source.country, Article.title)
            .select_from(Article)
            .join(Source, Article.source_id == Source.id)
            .where(Article.status == ArticleStatus.PUBLISHED,
                   Source.country.in_(list(keyword_buckets.keys())))
            .limit(500)
        )
        for tr in title_rows:
            cname = tr.country
            if cname in keyword_buckets and tr.title:
                words = re.findall(r'\b[a-zA-Z]{3,}\b', tr.title.lower())
                keyword_buckets[cname].update(w for w in words if w not in STOP_WORDS)

    # Secondary: articles without source country
    sec_query = select(Article.title, Article.summary).where(
        Article.status == ArticleStatus.PUBLISHED,
        Article.source_id.is_(None) | (
            select(Source.id).where(
                Source.id == Article.source_id,
                (Source.country.is_(None)) | (Source.country == "")
            ).exists()
        )
    ).order_by(desc(Article.published_at)).limit(200)
    if category:
        sec_query = sec_query.join(Category, Article.category_id == Category.id).where(Category.slug == category)
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        sec_query = sec_query.where(Article.published_at >= cutoff)

    rows2 = await db.execute(sec_query)
    for row in rows2:
        combined = f"{row.title or ''} {row.summary or ''}"
        for c in extract_countries(combined):
            if c in country_data:
                country_data[c]["cnt"] += 1

    countries = []
    for name, info in country_data.items():
        cnt = info["cnt"]
        countries.append({
            "country": name,
            "count": cnt,
            "lat": info["lat"],
            "lng": info["lng"],
            "severity": "high" if cnt > 50 else "medium" if cnt > 20 else "low",
            "sentiment": info["sentiment"],
            "top_keywords": [w for w, _ in keyword_buckets.get(name, Counter()).most_common(5)],
        })
    countries.sort(key=lambda x: x["count"], reverse=True)
    return {"countries": countries, "total": sum(c["count"] for c in countries)}


@router.get("/geo/{country}/articles", response_model=ArticleListOut)
async def get_country_articles(
    country: str,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return articles for a specific country."""
    # Resolve country aliases
    resolved = country
    for alias, target in COUNTRY_ALIASES.items():
        if alias.lower() == country.lower():
            resolved = target
            break
    # Find articles whose source country matches
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .join(Source, Article.source_id == Source.id)
        .where(Article.status == ArticleStatus.PUBLISHED,
               Source.country == resolved)
    )
    if category:
        query = query.join(Category, Article.category_id == Category.id).where(Category.slug == category)

    total_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar()

    query = query.order_by(desc(Article.published_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    return ArticleListOut(articles=articles, total=total or 0, page=page, limit=limit)

@router.get("/", response_model=ArticleListOut)
async def get_articles(
    category: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
    country: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.status == ArticleStatus.PUBLISHED)
    )

    if category:
        query = query.join(Category).where(Category.slug == category)
    if source:
        query = query.join(Source).where(Source.name == source)
    if country:
        resolved = country
        for alias, target in COUNTRY_ALIASES.items():
            if alias.lower() == country.lower():
                resolved = target
                break
        query = query.join(Source).where(Source.country == resolved)
    if q:
        search_terms = q.strip().split()
        for term in search_terms[:5]:
            pattern = f"%{term}%"
            query = query.where(
                or_(
                    Article.title.ilike(pattern),
                    Article.summary.ilike(pattern),
                    Article.author.ilike(pattern),
                )
            )

    total_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar()

    query = query.order_by(desc(Article.published_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    return ArticleListOut(articles=articles, total=total or 0, page=page, limit=limit)


@router.get("/trending", response_model=ArticleListOut)
async def get_trending(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.status == ArticleStatus.PUBLISHED)
        .order_by(desc(Article.view_count), desc(Article.published_at))
        .limit(limit)
    )
    result = await db.execute(query)
    articles = result.scalars().all()
    return ArticleListOut(articles=articles, total=len(articles), page=1, limit=limit)


@router.get("/ai-insights")
async def get_ai_insights(db: AsyncSession = Depends(get_db)):
    avg_q = select(func.avg(Article.sentiment_score)).where(Article.status == ArticleStatus.PUBLISHED)
    avg_sent = (await db.execute(avg_q)).scalar() or 28

    cat_q = (
        select(Category.name, func.count(Article.id).label("count"), func.avg(Article.sentiment_score).label("sent"))
        .select_from(Article)
        .join(Category, Article.category_id == Category.id)
        .where(Article.status == ArticleStatus.PUBLISHED)
        .group_by(Category.name)
    )
    cat_rows = await db.execute(cat_q)
    categories = [{"category": r.name, "count": r.count, "sentiment": round(r.sent or 0)} for r in cat_rows]

    titles_q = select(Article.title).where(Article.status == ArticleStatus.PUBLISHED).limit(200)
    titles = [t[0] for t in (await db.execute(titles_q)).all() if t[0]]
    from ..ai.processor import extract_keywords
    keywords = extract_keywords(" ".join(titles), top_n=12)

    return {
        "overall_sentiment": round(float(avg_sent)),
        "risk_index": max(5, min(95, 100 - round(float(avg_sent)))),
        "categories": categories,
        "top_topics": keywords or ["AI Infrastructure", "Clean Energy", "Markets", "Space"],
    }

@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article).options(selectinload(Article.category), selectinload(Article.source)).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.view_count = (article.view_count or 0) + 1
    await db.commit()

    return article
