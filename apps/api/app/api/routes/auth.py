"""Authentication & 2FA endpoints (spec FR-02)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import (
    REFRESH_TOKEN,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    totp_provisioning_uri,
    verify_totp,
)
from app.models.organization import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenPair,
    TotpEnrollResponse,
    TotpVerifyRequest,
)
from app.schemas.user import UserRead
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입 — 조직 + 소유자 계정 생성",
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await user_service.get_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = await user_service.register(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        company_name=payload.company_name,
    )
    return RegisterResponse(user=UserRead.model_validate(user), tokens=_issue_tokens(user))


@router.post("/login", response_model=TokenPair, summary="로그인 (2FA 시 totp_code 필요)")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if user.mfa_enabled:
        if not payload.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOTP code required",
            )
        if not user.totp_secret or not verify_totp(user.totp_secret, payload.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenPair, summary="토큰 갱신")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != REFRESH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    try:
        user = await user_service.get_by_id(db, uuid.UUID(data["sub"]))
    except (ValueError, KeyError):
        user = None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    return _issue_tokens(user)


@router.get("/me", response_model=UserRead, summary="현재 사용자 정보")
async def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── 2FA enrollment ───────────────────────────────────────────
@router.post(
    "/2fa/enroll",
    response_model=TotpEnrollResponse,
    summary="2FA 등록 시작 — 시크릿/프로비저닝 URI 발급",
)
async def enroll_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    secret = generate_totp_secret()
    current_user.totp_secret = secret  # stored but not yet active until verified
    await db.commit()
    return TotpEnrollResponse(
        secret=secret,
        provisioning_uri=totp_provisioning_uri(secret, current_user.email),
    )


@router.post(
    "/2fa/verify",
    response_model=MessageResponse,
    summary="2FA 활성화 — 첫 코드 검증",
)
async def verify_2fa(
    payload: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA enrollment not started",
        )
    if not verify_totp(current_user.totp_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code",
        )
    current_user.mfa_enabled = True
    await db.commit()
    return MessageResponse(detail="2FA enabled")


@router.post(
    "/2fa/disable",
    response_model=MessageResponse,
    summary="2FA 비활성화",
)
async def disable_2fa(
    payload: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.mfa_enabled or not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled",
        )
    if not verify_totp(current_user.totp_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code",
        )
    current_user.mfa_enabled = False
    current_user.totp_secret = None
    await db.commit()
    return MessageResponse(detail="2FA disabled")
