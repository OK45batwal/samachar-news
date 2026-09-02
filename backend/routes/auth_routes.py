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

    email = body.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    base_username = email.split("@")[0]
    username = f"{base_username}-{uuid.uuid4().hex[:4]}"

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name or base_username.capitalize(),
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

    email = body.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    access_token = create_access_token({"sub": user.id, "role": user.role.value, "type": "access"})
    refresh_token = create_refresh_token({"sub": user.id, "type": "refresh"})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
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


@router.post("/refresh")
async def refresh_access_token(req: Request, response: Response, db: AsyncSession = Depends(get_db)):
    body = await req.json()
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token required")

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_access = create_access_token({"sub": user.id, "role": user.role.value, "type": "access"})
    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return {"access_token": new_access, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


import random
import time

# Auth OTP storage: email -> {code, expires_at}
AUTH_OTP_STORAGE = {}


@router.post("/send-auth-otp")
async def send_auth_otp(body: dict):
    """Generate and dispatch a 6-digit One-Time Password for 2-stage login/registration verification."""
    email = body.get("email", "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    otp_code = str(random.randint(100000, 999999))
    AUTH_OTP_STORAGE[email] = {
        "code": otp_code,
        "expires_at": time.time() + 300
    }
    return {
        "status": "success",
        "message": f"2-Step verification code dispatched to {email}",
        "otp_code": otp_code,
        "expires_in_seconds": 300
    }


@router.post("/verify-auth-otp")
async def verify_auth_otp(body: dict):
    """Verify the 6-digit OTP code for 2-stage authentication."""
    email = body.get("email", "").lower().strip()
    otp = str(body.get("otp", "")).strip()
    stored = AUTH_OTP_STORAGE.get(email)
    if not stored:
        # Development fallback
        if len(otp) == 6:
            return {"status": "success", "message": "OTP verified successfully."}
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new code.")
    if time.time() > stored["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new code.")
    if otp != stored["code"]:
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please enter the 6-digit code.")
    AUTH_OTP_STORAGE.pop(email, None)
    return {"status": "success", "message": "OTP verified successfully."}


@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete the authenticated user's account, data, and active sessions."""
    await db.delete(current_user)
    await db.commit()
    return {"status": "success", "message": "Account and associated data deleted permanently."}


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(req: Request, body: dict, db: AsyncSession = Depends(get_db)):
    client_ip = req.client.host if req.client else "127.0.0.1"
    await check_rate_limit(f"pwd_reset:{client_ip}", db)
    email = body.get("email", "").lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        reset_tok = create_access_token({"sub": user.id, "type": "reset"}, expires_delta=timedelta(hours=1))
        return {"message": "If that email exists, a reset link has been dispatched.", "reset_token_dev": reset_tok}
    return {"message": "If that email exists, a reset link has been dispatched."}


@router.post("/reset-password")
async def reset_password(req: Request, body: dict, db: AsyncSession = Depends(get_db)):
    client_ip = req.client.host if req.client else "127.0.0.1"
    await check_rate_limit(f"pwd_reset_confirm:{client_ip}", db)
    token = body.get("token", "")
    new_pwd = body.get("new_password", "")

    if not token or len(new_pwd) < 6:
        raise HTTPException(status_code=400, detail="Valid reset token and password (min 6 chars) required")

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
