from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth.auth import get_current_user
from ..database import get_db
from ..models.models import Article, Bookmark, User
from ..schemas import BookmarkCreate, BookmarkOut

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


@router.get("/", response_model=List[BookmarkOut])
async def get_user_bookmarks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Bookmark)
        .options(selectinload(Bookmark.article).selectinload(Article.category), selectinload(Bookmark.article).selectinload(Article.source))
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=BookmarkOut, status_code=201)
async def create_bookmark(
    body: BookmarkCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check article exists
    art = await db.execute(select(Article).where(Article.id == body.article_id))
    if not art.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Article not found")

    # Check already bookmarked
    existing = await db.execute(
        select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.article_id == body.article_id)
    )
    b = existing.scalar_one_or_none()
    if b:
        return b

    bookmark = Bookmark(
        user_id=user.id,
        article_id=body.article_id,
        folder=body.folder or "default",
        notes=body.notes,
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return bookmark


@router.delete("/{article_id}")
async def delete_bookmark(
    article_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark).where(Bookmark.user_id == user.id, Bookmark.article_id == article_id)
    )
    bookmark = result.scalar_one_or_none()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    await db.delete(bookmark)
    await db.commit()
    return {"message": "Bookmark removed"}
