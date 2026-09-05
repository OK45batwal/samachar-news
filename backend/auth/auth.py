import time
from datetime import timedelta
from typing import Optional

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.models import RevokedToken, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

REVOKED_TOKENS: set[str] = set()


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = int(time.time()) + int((expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).total_seconds())
    token_type = to_encode.get("type", "access")
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = int(time.time()) + int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def revoke_token(token: str, db: Optional[AsyncSession] = None) -> None:
    if not token:
        return
    REVOKED_TOKENS.add(token)
    if db is not None:
        try:
            db.add(RevokedToken(token=token))
            await db.commit()
        except Exception:
            await db.rollback()


async def is_token_revoked(token: str, db: Optional[AsyncSession] = None) -> bool:
    if not token:
        return False
    if token in REVOKED_TOKENS:
        return True
    if db is not None:
        try:
            result = await db.execute(select(RevokedToken).where(RevokedToken.token == token))
            if result.scalar_one_or_none() is not None:
                REVOKED_TOKENS.add(token)
                return True
        except Exception:
            pass
    return False


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if await is_token_revoked(token, db):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin authorization required")
    return current_user

