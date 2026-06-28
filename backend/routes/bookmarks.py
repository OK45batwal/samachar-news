from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..database import get_db
from ..models.models import Bookmark, Article
from ..auth.auth import get_current_user

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])

@router.get("/")
async def get_bookmarks(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Bookmark).where(Bookmark.user_id == user.id)
    )
    return result.scalars().all()

@router.post("/")
async def add_bookmark(article_id: int, folder: str = "default", user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    article = await db.execute(select(Article).where(Article.id == article_id))
    if not article.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Article not found")

    existing = await db.execute(
        select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.article_id == article_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already bookmarked")

    bm = Bookmark(user_id=user.id, article_id=article_id, folder=folder)
    db.add(bm)
    await db.commit()
    return {"status": "ok"}

@router.delete("/{article_id}")
async def remove_bookmark(article_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(
        delete(Bookmark).where(Bookmark.user_id == user.id, Bookmark.article_id == article_id)
    )
    await db.commit()
    return {"status": "ok"}
