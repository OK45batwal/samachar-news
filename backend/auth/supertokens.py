from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python import InputAppInfo, SupertokensConfig, init
from supertokens_python.recipe import emailpassword, session, thirdparty
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.thirdparty import (
    ProviderClientConfig,
    ProviderConfig,
    ProviderInput,
)

from ..config import settings
from ..database import get_db
from ..models.models import User


def _thirdparty_providers():
    """Build provider list from env vars. Providers without client_id are skipped."""
    providers = []
    if settings.GOOGLE_CLIENT_ID:
        providers.append(
            ProviderInput(
                config=ProviderConfig(
                    third_party_id="google",
                    clients=[
                        ProviderClientConfig(
                            client_id=settings.GOOGLE_CLIENT_ID,
                            client_secret=settings.GOOGLE_CLIENT_SECRET or "",
                        )
                    ],
                ),
            ),
        )
    if settings.GITHUB_CLIENT_ID:
        providers.append(
            ProviderInput(
                config=ProviderConfig(
                    third_party_id="github",
                    clients=[
                        ProviderClientConfig(
                            client_id=settings.GITHUB_CLIENT_ID,
                            client_secret=settings.GITHUB_CLIENT_SECRET or "",
                        )
                    ],
                ),
            ),
        )
    if settings.FACEBOOK_CLIENT_ID:
        providers.append(
            ProviderInput(
                config=ProviderConfig(
                    third_party_id="facebook",
                    clients=[
                        ProviderClientConfig(
                            client_id=settings.FACEBOOK_CLIENT_ID,
                            client_secret=settings.FACEBOOK_CLIENT_SECRET or "",
                        )
                    ],
                ),
            ),
        )
    return providers


def init_supertokens():
    if not settings.SUPERTOKENS_CONNECTION_URI:
        return

    providers = _thirdparty_providers()
    recipe_list = [
        emailpassword.init(),
        session.init(
            anti_csrf="NONE",
            cookie_secure=settings.API_DOMAIN.startswith("https://"),
        ),
    ]
    if providers:
        recipe_list.insert(0, thirdparty.init(sign_in_and_up_feature=thirdparty.SignInAndUpFeature(providers=providers)))

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
        recipe_list=recipe_list,
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
