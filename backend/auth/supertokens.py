from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python import InputAppInfo, SupertokensConfig, get_all_cors_headers, init
from supertokens_python.recipe import emailpassword, session
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session

from ..config import settings
from ..database import get_db
from ..models.models import User


def init_supertokens():
    if not settings.SUPERTOKENS_CONNECTION_URI:
        return

    init(
        app_info=InputAppInfo(
            app_name="Samachar News",
            api_domain=settings.API_DOMAIN,
            website_domain=settings.WEBSITE_DOMAIN,
            api_base_path="/auth",
            website_base_path="/auth",
        ),
        supertokens_config=SupertokensConfig(
            connection_uri=settings.SUPERTOKENS_CONNECTION_URI,
        ),
        framework="fastapi",
        recipe_list=[
            emailpassword.init(),
            session.init(
                anti_csrf="NONE",
                cookie_secure=settings.API_DOMAIN.startswith("https://"),
            ),
        ],
        mode="asgi",
    )


async def get_st_session(
    session_container: SessionContainer = Depends(verify_session()),
) -> SessionContainer:
    return session_container


async def get_current_user(
    session_container: SessionContainer = Depends(verify_session()),
    db: AsyncSession = Depends(get_db),
) -> User:
    st_user_id = session_container.get_user_id()
    result = await db.execute(select(User).where(User.id == st_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")
    return user
