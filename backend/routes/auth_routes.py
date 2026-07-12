import secrets
import time
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models.models import User
from ..services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])

CSRF_TOKENS = {}
CSRF_EXPIRY = 3600  # 1 hour


def _generate_csrf() -> str:
    return secrets.token_urlsafe(32)


def _validate_csrf(request: Request):
    token = request.headers.get("x-csrf-token") or request.headers.get("X-CSRF-Token")
    if not token:
        raise HTTPException(status_code=403, detail="Missing CSRF token")
    entry = CSRF_TOKENS.get(token)
    if not entry:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    if entry["exp"] < time.time():
        del CSRF_TOKENS[token]
        raise HTTPException(status_code=403, detail="CSRF token expired")
    del CSRF_TOKENS[token]


def _set_csrf_cookie(response: Response):
    token = _generate_csrf()
    CSRF_TOKENS[token] = {"exp": time.time() + CSRF_EXPIRY}
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        secure=True,
        samesite="lax",
        path="/",
        max_age=CSRF_EXPIRY,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    username: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def valid_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


def _set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=86400 * 7,
    )


@router.post("/login")
async def login(data: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    await check_rate_limit(f"{request.client.host}:login", db)
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    token = create_access_token({"sub": user.id})
    _set_token_cookie(response, token)
    _set_csrf_cookie(response)
    return UserResponse.model_validate(user)


@router.post("/register", status_code=201)
async def register(data: RegisterRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    await check_rate_limit(f"{request.client.host}:register", db)
    existing = await db.execute(
        select(User).where((User.email == data.email) | (User.username == data.email.split("@")[0]))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    username = data.email.split("@")[0]
    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        username=username,
        full_name=data.full_name or username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    _set_token_cookie(response, token)
    _set_csrf_cookie(response)
    return UserResponse.model_validate(user)


@router.post("/logout")
async def logout(request: Request, response: Response):
    _validate_csrf(request)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="csrf_token", path="/")
    return {"status": "ok"}


@router.get("/ws-token")
async def get_ws_token(user: User = Depends(get_current_user)):
    token = create_access_token(
        {"sub": user.id, "type": "ws"},
        expires_delta=timedelta(minutes=5),
    )
    return {"token": token}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
