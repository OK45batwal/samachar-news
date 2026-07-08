from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import create_access_token
from ..auth.supertokens import get_current_user, get_st_session
from ..database import get_db
from ..models.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    username: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime


class CreateProfileRequest(BaseModel):
    email: str
    username: str
    full_name: str | None = None

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format")
        return v


@router.post("/profile", response_model=UserResponse, status_code=201)
async def create_profile(
    data: CreateProfileRequest,
    session=Depends(get_st_session),
    db: AsyncSession = Depends(get_db),
):
    st_user_id = session.get_user_id()

    existing = await db.execute(
        select(User).where(
            (User.email == data.email) | (User.username == data.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email or username already exists")

    profile = User(
        id=st_user_id,
        email=data.email,
        username=data.username,
        full_name=data.full_name,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return UserResponse.model_validate(profile)


@router.get("/ws-token")
async def get_ws_token(
    session=Depends(get_st_session),
):
    token = create_access_token(
        {"sub": session.get_user_id()},
        expires_delta=timedelta(minutes=5),
    )
    return {"token": token}


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(user)
