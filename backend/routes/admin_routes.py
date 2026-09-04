from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import get_current_user, require_admin
from ..database import get_db
from ..models.models import Article, Category, Source, User, UserRole
from ..services.news_service import ingest_all_feeds

router = APIRouter(prefix="/api/admin", tags=["admin"])


_require_admin = require_admin


@router.get("/overview")
async def get_admin_overview(
    user: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    articles = (await db.execute(select(func.count(Article.id)))).scalar() or 0
    sources = (await db.execute(select(func.count(Source.id)))).scalar() or 0
    categories = (await db.execute(select(func.count(Category.id)))).scalar() or 0

    return {
        "users": users,
        "articles": articles,
        "sources": sources,
        "categories": categories,
    }


@router.post("/trigger-ingestion")
async def trigger_ingestion(user: User = Depends(_require_admin)):
    result = await ingest_all_feeds()
    return {"message": "Ingestion triggered and completed", "result": result}
