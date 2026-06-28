from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete
from pydantic import BaseModel

from ..database import get_db
from ..models.models import Article, Category, Source, User, Bookmark, ArticleStatus, UserRole
from ..auth.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def require_admin(user=Depends(get_current_user)):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

class ArticleCreate(BaseModel):
    title: str
    summary: Optional[str] = ""
    content: Optional[str] = ""
    image_url: Optional[str] = ""
    source_url: Optional[str] = ""
    author: Optional[str] = ""
    category_slug: Optional[str] = ""
    source_name: Optional[str] = ""
    status: str = "draft"

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None

@router.get("/dashboard")
async def admin_dashboard(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    users_q = select(func.count()).select_from(User)
    articles_q = select(func.count()).select_from(Article)
    published_q = select(func.count()).where(Article.status == ArticleStatus.PUBLISHED)
    bookmarks_q = select(func.count()).select_from(Bookmark)

    users = (await db.execute(users_q)).scalar() or 0
    articles = (await db.execute(articles_q)).scalar() or 0
    published = (await db.execute(published_q)).scalar() or 0
    bookmarks = (await db.execute(bookmarks_q)).scalar() or 0

    return {
        "total_users": users,
        "total_articles": articles,
        "published_articles": published,
        "total_bookmarks": bookmarks,
    }

@router.get("/articles")
async def admin_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    q = select(Article).order_by(desc(Article.created_at)).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    articles = result.scalars().all()

    count_q = select(func.count()).select_from(Article)
    total = (await db.execute(count_q)).scalar() or 0

    return {"articles": articles, "total": total, "page": page, "limit": limit}

@router.post("/articles")
async def create_article(
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    from ..utils.utils import slugify
    slug_base = slugify(data.title) or "untitled"
    slug = slug_base
    counter = 1
    while True:
        ck = await db.execute(select(Article).where(Article.slug == slug))
        if not ck.scalar_one_or_none():
            break
        slug = f"{slug_base[:190]}-{counter}"
        counter += 1

    category_id = None
    if data.category_slug:
        cat = await db.execute(select(Category).where(Category.slug == data.category_slug))
        cat = cat.scalar_one_or_none()
        if cat:
            category_id = cat.id

    source_id = None
    if data.source_name:
        src = await db.execute(select(Source).where(Source.name == data.source_name))
        src = src.scalar_one_or_none()
        if not src:
            src = Source(name=data.source_name, is_active=True)
            db.add(src)
            await db.commit()
            await db.refresh(src)
        source_id = src.id

    status = ArticleStatus.DRAFT
    if data.status == "published":
        status = ArticleStatus.PUBLISHED
    elif data.status == "archived":
        status = ArticleStatus.ARCHIVED

    article = Article(
        title=data.title,
        slug=slug,
        summary=data.summary,
        content=data.content,
        image_url=data.image_url,
        source_url=data.source_url,
        author=data.author,
        status=status,
        category_id=category_id,
        source_id=source_id,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article

@router.put("/articles/{article_id}")
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    for field, val in data.model_dump(exclude_none=True).items():
        if field == "status":
            val = ArticleStatus(val)
        setattr(article, field, val)

    await db.commit()
    await db.refresh(article)
    return article

@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)
    await db.commit()
    return {"status": "ok"}

@router.get("/users")
async def admin_users(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return {"users": result.scalars().all()}

@router.get("/categories")
async def admin_categories(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await db.execute(select(Category))
    return {"categories": result.scalars().all()}
