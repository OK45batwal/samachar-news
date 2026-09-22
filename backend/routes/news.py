import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth.auth import require_admin
from ..database import get_db
from ..models.models import Article, ArticleStatus, Category, Source, User
from ..ai.intelligence import (
    answer_article_question,
    analyze_wire_perspectives,
    calculate_personal_impact,
    generate_cognitive_depths,
)
from ..schemas import (
    ArticleAskRequest,
    ArticleAskResponse,
    ArticleListOut,
    ArticleOut,
    CategoryOut,
    CognitiveDepthResponse,
    PerspectivePrismResponse,
    PersonalImpactRequest,
    PersonalImpactResponse,
    SourceOut,
)

logger = logging.getLogger("samachar.news")
router = APIRouter(prefix="/api/news", tags=["News"])


def _escape_like(text: str) -> str:
    """Escape SQL LIKE wildcards (%, _) and backslash to prevent wildcard injection."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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
        safe_source = _escape_like(source)
        query = query.join(Article.source).where(Source.name.ilike(f"%{safe_source}%", escape="\\"))

    if q:
        safe_q = _escape_like(q)
        kw = f"%{safe_q}%"
        query = query.where(
            or_(
                Article.title.ilike(kw, escape="\\"),
                Article.summary.ilike(kw, escape="\\"),
                Article.content.ilike(kw, escape="\\"),
            )
        )

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
    distinct_countries = (await db.execute(select(func.count(func.distinct(Source.country))))).scalar() or 1
    avg_cred = (await db.execute(select(func.avg(Article.credibility_score)))).scalar()
    credibility_avg = round(float(avg_cred), 1) if avg_cred is not None else 92.0

    return {
        "total_articles": art_count,
        "verified_articles": verified_count,
        "verified_count": verified_count,
        "active_sources": src_count,
        "truth_index_avg": credibility_avg,
        "credibility_avg": credibility_avg,
        "countries_covered": max(distinct_countries, 1),
    }


@router.post("/sync")
async def trigger_news_sync(admin_user: User = Depends(require_admin)):
    """Trigger on-demand live RSS feed ingestion and truth evaluation (admin only)."""
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
    except Exception as e:
        logger.warning("Failed to update view_count for article %s: %s", id, e)
        await db.rollback()

    return article


@router.get("/{id}/depth", response_model=CognitiveDepthResponse)
async def get_article_depth(id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve 4-tier Cognitive Depth Matrix (15s Radar, 2m Brief, Deep Dive, ELI5)."""
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.id == id)
    )
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    depths = generate_cognitive_depths(
        title=article.title,
        summary=article.summary or "",
        content=article.content or "",
        key_claims=article.key_claims or [],
        category=article.category.name if article.category else None,
        source=article.source.name if article.source else None,
        credibility_score=article.credibility_score or 88,
    )
    return depths


@router.post("/{id}/ask", response_model=ArticleAskResponse)
async def ask_article(id: int, payload: ArticleAskRequest, db: AsyncSession = Depends(get_db)):
    """Socratic in-situ Copilot: answer contextual queries bounded by the article's ground truth."""
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.id == id)
    )
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    art_dict = {
        "title": article.title,
        "summary": article.summary or "",
        "content": article.content or "",
        "key_claims": article.key_claims or [],
        "category_name": article.category.name if article.category else "General",
        "source_name": article.source.name if article.source else "Wire Bureau",
        "credibility_score": article.credibility_score or 88,
        "sensationalism_score": article.sensationalism_score or 12,
        "bias_spectrum": article.bias_spectrum or "Neutral Analytic",
    }

    ans = answer_article_question(
        article_dict=art_dict,
        question=payload.question,
        selected_context=payload.selected_context,
    )
    return ans


@router.get("/{id}/perspectives", response_model=PerspectivePrismResponse)
async def get_perspectives(id: int, db: AsyncSession = Depends(get_db)):
    """Multi-wire Perspective Prism & Omission Radar for multi-angle comparative journalism."""
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.id == id)
    )
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    art_dict = {
        "title": article.title,
        "summary": article.summary or "",
        "content": article.content or "",
        "key_claims": article.key_claims or [],
        "category_name": article.category.name if article.category else "General",
        "source_name": article.source.name if article.source else "Wire Bureau",
        "credibility_score": article.credibility_score or 88,
    }

    return analyze_wire_perspectives(art_dict)


@router.post("/{id}/impact", response_model=PersonalImpactResponse)
async def get_personal_impact(id: int, payload: PersonalImpactRequest, db: AsyncSession = Depends(get_db)):
    """Personal Impact Simulator for citizen/worker/investor personas."""
    query = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.source))
        .where(Article.id == id)
    )
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    art_dict = {
        "title": article.title,
        "summary": article.summary or "",
        "content": article.content or "",
        "category_name": article.category.name if article.category else "General",
    }

    return calculate_personal_impact(art_dict, persona=payload.persona)
