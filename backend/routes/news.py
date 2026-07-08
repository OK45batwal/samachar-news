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
}


@router.get("/geo")
async def get_geo_events(db: AsyncSession = Depends(get_db)):
    """Return events grouped by country with approximate coordinates."""
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
    countries = []
    for row in rows:
        cnt = row.cnt
        lat, lng = COUNTRY_COORDS.get(row.country)
        if lat is not None:
            countries.append({
                "country": row.country,
                "count": cnt,
                "lat": lat,
                "lng": lng,
                "severity": "high" if cnt > 50 else "medium" if cnt > 20 else "low",
            })
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
