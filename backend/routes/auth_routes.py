import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    revoke_token,
    verify_password,
)
from ..config import settings
from ..database import get_db
from ..models.models import User, UserRole
from ..schemas import UserCreate, UserLogin, UserOut
from ..services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(req: Request, body: UserCreate, db: AsyncSession = Depends(get_db)):
    client_ip = req.client.host if req.client else "127.0.0.1"
    await check_rate_limit(f"reg:{client_ip}", db)

    # Check email exists
    result = await db.execute(select(User).where(User.email == body.email.lower().strip()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email is already registered")

    # Generate or sanitize username
    base_username = body.email.split("@")[0]
    username = base_username
    counter = 1
    while True:
        check_u = await db.execute(select(User).where(User.username == username))
        if not check_u.scalar_one_or_none():
            break
        username = f"{base_username}-{uuid.uuid4().hex[:4]}"
        counter += 1

    user = User(
        email=body.email.lower().strip(),
        username=username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name or username,
        role=UserRole.USER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login")
async def login(req: Request, body: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    client_ip = req.client.host if req.client else "127.0.0.1"
    await check_rate_limit(f"login:{client_ip}", db)

    result = await db.execute(select(User).where(User.email == body.email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token({"sub": user.id, "role": user.role.value, "type": "access"})
    refresh_token = create_refresh_token({"sub": user.id, "type": "refresh"})

    is_https = req.url.scheme == "https" or req.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=is_https,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
        },
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("access_token")
    if not token and request.headers.get("authorization"):
        parts = request.headers.get("authorization").split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if token:
        revoke_token(token)

    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("/ws-token")
async def get_ws_token(user: User = Depends(get_current_user)):
    """Generate scoped token for real-time WebSocket connection."""
    token = create_access_token({"sub": user.id, "role": user.role.value, "type": "ws"}, expires_delta=timedelta(hours=2))
    return {"token": token, "expires_in": 7200}


@router.post("/forgot-password")
async def forgot_password(req: Request, body: dict, db: AsyncSession = Depends(get_db)):
    await check_rate_limit(f"pwd_reset:{req.client.host}", db)
    email = body.get("email", "").lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        reset_token = create_access_token({"sub": user.id, "type": "reset"}, expires_delta=timedelta(minutes=30))
        return {
            "message": f"If an account exists for {email}, a reset link has been dispatched.",
            "reset_token": reset_token,
        }
    return {"message": f"If an account exists for {email}, a reset link has been dispatched."}


@router.post("/reset-password")
async def reset_password(req: Request, body: dict, db: AsyncSession = Depends(get_db)):
    await check_rate_limit(f"pwd_reset_confirm:{req.client.host}", db)
    token = body.get("token", "")
    new_pwd = body.get("new_password", "")

    if not token or len(new_pwd) < 8:
        raise HTTPException(status_code=400, detail="Valid reset token and password (min 8 chars) required")

    try:
        payload = decode_token(token)
        if payload.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=400, detail="Expired or invalid reset token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_pwd)
    revoke_token(token)
    await db.commit()
    return {"message": "Password updated successfully. You can now log in."}
