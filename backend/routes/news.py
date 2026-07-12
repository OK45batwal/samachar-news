import difflib
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.models import Article, ArticleStatus, Category, Source
from ..schemas import ArticleListOut, ArticleOut

router = APIRouter(prefix="/api/news", tags=["news"])

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


def _fuzzy_match_country(text: str) -> list[str]:
    """Fuzzy-match country names when exact match fails."""
    found = set()
    words = re.findall(r'\b(\w+)\b', text.lower())
    country_names = list(COUNTRY_COORDS.keys())
    for target in country_names:
        if target.lower() in words:
            found.add(target)
    # Levenshtein-like: allow single-char diffs on 3+ char words
    for target in country_names:
        if len(target) < 4:
            continue
        tl = target.lower()
        for w in words:
            if len(w) < 3:
                continue
            if difflib.SequenceMatcher(None, tl, w).ratio() > 0.85:
                found.add(target)
                break
    for alias, target in COUNTRY_ALIASES.items():
        al = alias.lower()
        if len(al) < 4:
            continue
        for w in words:
            if len(w) < 3:
                continue
            if difflib.SequenceMatcher(None, al, w).ratio() > 0.85:
                found.add(target)
                break
    return list(found)


def extract_countries(text: str) -> list[str]:
    """Match country names in text using keyword search and fuzzy fallback."""
    if not text:
        return []
    found = set()
    upper = text.upper()
    for name in COUNTRY_COORDS:
        alias = COUNTRY_ALIASES.get(name, name)
        if alias.upper() in upper:
            found.add(name)
    for alias, target in COUNTRY_ALIASES.items():
        if alias.upper() in upper:
            found.add(target)
    # Fuzzy fallback for unclear mentions
    if not found:
        fuzzy = _fuzzy_match_country(text)
        found.update(fuzzy)
    # Filter out EU (too broad)
    found.discard("EU")
    return list(found)


@router.get("/geo")
async def get_geo_events(db: AsyncSession = Depends(get_db)):
    """Return events grouped by country with approximate coordinates.
    Uses source country and also extracts country mentions from article content."""
    # Primary: group by source country
    rows = await db.execute(
        text("""
            SELECT s.country, COUNT(*) as cnt
            FROM articles a
            JOIN sources s ON a.source_id = s.id
            WHERE a.status = 'published' AND s.country IS NOT NULL AND s.country != ''
            GROUP BY s.country
            ORDER BY cnt DESC
        """)
    )
    country_counts = {}
    for row in rows:
        cnt = row.cnt
        lat, lng = COUNTRY_COORDS.get(row.country)
        if lat is not None:
            country_counts[row.country] = cnt

    # Secondary: for articles without source country, extract from content
    rows2 = await db.execute(
        text("""
            SELECT a.title, a.summary
            FROM articles a
            WHERE a.status = 'published'
            AND (a.source_id IS NULL OR EXISTS (
                SELECT 1 FROM sources s WHERE s.id = a.source_id AND (s.country IS NULL OR s.country = '')
            ))
            ORDER BY a.published_at DESC
            LIMIT 200
        """)
    )
    for row in rows2:
        combined = f"{row.title or ''} {row.summary or ''}"
        for c in extract_countries(combined):
            country_counts[c] = country_counts.get(c, 0) + 1

    countries = []
    for name, cnt in country_counts.items():
        lat, lng = COUNTRY_COORDS.get(name)
        if lat is not None:
            countries.append({
                "country": name,
                "count": cnt,
                "lat": lat,
                "lng": lng,
                "severity": "high" if cnt > 50 else "medium" if cnt > 20 else "low",
            })
    countries.sort(key=lambda x: x["count"], reverse=True)
    return {"countries": countries, "total": sum(c["count"] for c in countries)}

@router.get("/", response_model=ArticleListOut)
async def get_articles(
    category: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
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
    if q:
        query = query.where(
            or_(Article.title.ilike(f"%{q}%"), Article.summary.ilike(f"%{q}%"))
        )

    total_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar()

    query = query.order_by(desc(Article.published_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    return ArticleListOut(articles=articles, total=total or 0, page=page, limit=limit)

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
