import hashlib
import hmac
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import create_access_token, decode_token, get_current_user, hash_password, verify_password
from ..config import settings
from ..database import get_db
from ..models.models import User
from ..services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])

CSRF_TOKENS = {}
CSRF_EXPIRY = 3600  # 1 hour


def _is_secure(request: Optional[Request] = None) -> bool:
    if settings.API_DOMAIN.startswith("https://"):
        return True
    if request:
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            return True
    return False


def _generate_csrf() -> str:
    raw = f"{secrets.token_hex(16)}.{int(time.time() + CSRF_EXPIRY)}"
    sig = hmac.new(settings.SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
    token = f"{raw}.{sig}"
    CSRF_TOKENS[token] = {"exp": time.time() + CSRF_EXPIRY}
    return token


def _validate_csrf(request: Request):
    token = request.headers.get("x-csrf-token") or request.headers.get("X-CSRF-Token")
    if not token:
        raise HTTPException(status_code=403, detail="Missing CSRF token")
    if token in CSRF_TOKENS:
        entry = CSRF_TOKENS[token]
        if entry["exp"] >= time.time():
            del CSRF_TOKENS[token]
            return
        del CSRF_TOKENS[token]
        raise HTTPException(status_code=403, detail="CSRF token expired")

    # Fallback: HMAC signature verification (handles server restarts gracefully)
    try:
        parts = token.split(".")
        if len(parts) == 3:
            rand_part, exp_str, sig = parts
            exp = int(exp_str)
            if exp >= time.time():
                raw = f"{rand_part}.{exp_str}"
                expected_sig = hmac.new(settings.SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
                if hmac.compare_digest(sig, expected_sig):
                    return
    except Exception:
        pass
    raise HTTPException(status_code=403, detail="Invalid CSRF token")


def _set_csrf_cookie(response: Response, request: Optional[Request] = None):
    token = _generate_csrf()
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        secure=_is_secure(request),
        samesite="lax",
        path="/",
        max_age=CSRF_EXPIRY,
    )


def _set_token_cookie(response: Response, token: str, request: Optional[Request] = None):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=_is_secure(request),
        samesite="lax",
        path="/",
        max_age=86400 * 7,
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


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def valid_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    preferences: Optional[dict] = None


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
    _set_token_cookie(response, token, request)
    _set_csrf_cookie(response, request)
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
    _set_token_cookie(response, token, request)
    _set_csrf_cookie(response, request)
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


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.username is not None and data.username != user.username:
        existing = await db.execute(select(User).where(User.username == data.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already taken")
        user.username = data.username
    if data.new_password:
        if not data.current_password or not verify_password(data.current_password, user.hashed_password or ""):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.hashed_password = hash_password(data.new_password)
    if data.preferences is not None:
        user.preferences = data.preferences

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if user:
        token = create_access_token({"sub": user.id, "type": "reset"}, expires_delta=timedelta(hours=1))
        return {
            "status": "ok",
            "message": "If email is registered, password reset token has been issued",
            "reset_token": token,
        }
    return {"status": "ok", "message": "If email is registered, password reset token has been issued"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.token)
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid reset token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return {"status": "ok", "message": "Password updated successfully"}
