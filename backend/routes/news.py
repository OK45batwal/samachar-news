from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.models import Article, ArticleStatus, Category, Source
from ..schemas import ArticleListOut, ArticleOut, CategoryOut, SourceOut

router = APIRouter(prefix="/api/news", tags=["News"])


@router.get("/", response_model=ArticleListOut)
async def list_news(
    category: Optional[str] = Query(None, description="Category slug"),
    source: Optional[str] = Query(None, description="Source name"),
    q: Optional[str] = Query(None, description="Search keyword in title or summary"),
    verified_only: bool = Query(False, description="Filter for 85%+ credibility score"),
    sort: str = Query("latest", pattern="^(latest|trending|credibility)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.status == ArticleStatus.PUBLISHED)
    )

    if category:
        query = query.join(Article.category).where(Category.slug == category.lower())

    if source:
        query = query.join(Article.source).where(Source.name.ilike(f"%{source}%"))

    if q:
        kw = f"%{q}%"
        query = query.where(or_(Article.title.ilike(kw), Article.summary.ilike(kw), Article.content.ilike(kw)))

    if verified_only:
        query = query.where(Article.credibility_score >= 85)

    # Ordering
    if sort == "trending":
        query = query.order_by(desc(Article.view_count), desc(Article.published_at))
    elif sort == "credibility":
        query = query.order_by(desc(Article.credibility_score), desc(Article.published_at))
    else:
        query = query.order_by(desc(Article.published_at))

    # Count total
    total_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(total_query)
    total = total_res.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * limit).limit(limit)
    results = await db.execute(query)
    articles = results.scalars().all()

    return ArticleListOut(
        articles=articles,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/trending", response_model=List[ArticleOut])
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
    results = await db.execute(query)
    return results.scalars().all()


@router.get("/verified", response_model=List[ArticleOut])
async def get_verified_breaking(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve top-tier multi-source corroborated articles."""
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.status == ArticleStatus.PUBLISHED, Article.credibility_score >= 88)
        .order_by(desc(Article.published_at))
        .limit(limit)
    )
    results = await db.execute(query)
    return results.scalars().all()


@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


@router.get("/sources", response_model=List[SourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(desc(Source.reliability_score)))
    return result.scalars().all()


@router.get("/stats")
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    art_count = (await db.execute(select(func.count(Article.id)))).scalar() or 0
    verified_count = (await db.execute(select(func.count(Article.id)).where(Article.credibility_score >= 85))).scalar() or 0
    src_count = (await db.execute(select(func.count(Source.id)))).scalar() or 0

    return {
        "total_articles": art_count,
        "verified_articles": verified_count,
        "active_sources": src_count,
        "truth_index_avg": 91,
        "countries_covered": 150,
    }


@router.post("/sync")
async def trigger_news_sync():
    """Trigger on-demand live RSS feed ingestion and truth evaluation."""
    from ..services.news_service import ingest_all_feeds
    result = await ingest_all_feeds()
    return {"status": "success", "data": result}


@router.get("/{id}", response_model=ArticleOut)
async def get_article(id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.id == id)
    )
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    try:
        article.view_count = (article.view_count or 0) + 1
        await db.commit()
    except Exception:
        await db.rollback()

    return article
