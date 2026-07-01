from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.models import Article, ArticleStatus, Category, Source
from ..schemas import ArticleListOut, ArticleOut

router = APIRouter(prefix="/api/news", tags=["news"])

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
