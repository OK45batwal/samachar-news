import logging
import random
import secrets
import uuid
from datetime import datetime, timedelta, timezone
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
from ..models.models import EmailOtp, User, UserRole
from ..schemas import UserCreate, UserLogin, UserOut
from ..services.email_service import send_password_reset_email, send_verification_otp_email
from ..services.rate_limit import check_rate_limit

logger = logging.getLogger("samachar.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _is_request_secure(req: Request) -> bool:
    """Check if request was transported via HTTPS or deployed in production."""
    if settings.ENVIRONMENT.lower() == "production":
        return True
    scheme = req.headers.get("x-forwarded-proto", req.url.scheme)
    return scheme.lower() == "https"



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
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token({"sub": user.id, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.id})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=_is_request_secure(req),
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
            "preferences": user.preferences,
        },
    }


@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": user.id, "role": user.role.value})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=_is_request_secure(request),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/send-auth-otp")
async def send_auth_otp(req: Request, body: dict, db: AsyncSession = Depends(get_db)):
    """Generate and dispatch a cryptographically secure 6-digit OTP code via email."""
    client_ip = req.client.host if req.client else "127.0.0.1"
    await check_rate_limit(f"send_otp:{client_ip}", db)

    email = body.get("email", "").lower().strip()
    name = body.get("name", "Reader").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    # Cryptographically secure 6-digit OTP code
    otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(minutes=10)

    # Persist in DB with reset attempt counter
    existing = await db.get(EmailOtp, email)
    if existing:
        existing.otp_code = otp_code
        existing.expires_at = expires_at
        existing.attempts = 0
        existing.created_at = now
    else:
        db.add(EmailOtp(email=email, otp_code=otp_code, expires_at=expires_at, attempts=0, created_at=now))
    await db.commit()

    # Dispatch email asynchronously
    await send_verification_otp_email(email, otp_code, name)

    return {
        "status": "success",
        "message": f"Security verification code dispatched to your email inbox: {email}",
        "expires_in_seconds": 600
    }


@router.post("/verify-auth-otp")
async def verify_auth_otp(req: Request, body: dict, db: AsyncSession = Depends(get_db)):
    """Verify 6-digit OTP code with attempts throttling and constant-time comparison."""
    client_ip = req.client.host if req.client else "127.0.0.1"
    await check_rate_limit(f"verify_otp:{client_ip}", db)

    email = body.get("email", "").lower().strip()
    otp = str(body.get("otp", "")).strip()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    stored = await db.get(EmailOtp, email)
    if not stored:
        raise HTTPException(status_code=400, detail="No OTP found. Please request a new code.")

    if now > stored.expires_at:
        await db.delete(stored)
        await db.commit()
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new code.")

    # Brute-force throttling: max 5 failed attempts allowed
    if stored.attempts >= 5:
        await db.delete(stored)
        await db.commit()
        raise HTTPException(
            status_code=429,
            detail="Too many incorrect OTP attempts. For security, please request a new verification code."
        )

    stored.attempts += 1

    # Constant-time comparison protects against timing side-channel attacks
    if not secrets.compare_digest(otp, stored.otp_code):
        await db.commit()
        remaining = max(0, 5 - stored.attempts)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining."
        )

    # Validated successfully - purge the OTP token
    await db.delete(stored)
    await db.commit()
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
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log out and revoke the current bearer token."""
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif request.cookies.get("access_token"):
        token = request.cookies.get("access_token")
    if token:
        await revoke_token(token, db)
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
        reset_token = create_access_token({"sub": user.id, "type": "reset"}, expires_delta=timedelta(hours=1))
        try:
            await send_password_reset_email(user.email, reset_token, user.full_name or "Reader")
        except Exception as e:
            logger.warning("Failed to dispatch password reset email to %s: %s", user.email, e)
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
    await revoke_token(token, db)
    await db.commit()
    return {"message": "Password updated successfully. You can now log in."}
