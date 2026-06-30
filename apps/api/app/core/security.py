"""Password hashing, JWT tokens, and TOTP (2FA) helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import pyotp
from jose import JWTError, jwt

from app.core.config import settings

ACCESS_TOKEN = "access"  # noqa: S105 - token type label, not a secret
REFRESH_TOKEN = "refresh"  # noqa: S105

# bcrypt only considers the first 72 bytes of the input; truncate explicitly
# so longer passphrases don't raise on bcrypt >= 4.x.
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


# ── Passwords ────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


# ── JWT ──────────────────────────────────────────────────────
def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject,
        ACCESS_TOKEN,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        REFRESH_TOKEN,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Returns the payload, or None if the token is invalid/expired."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


# ── TOTP (2FA) ───────────────────────────────────────────────
def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, account_name: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name, issuer_name=settings.app_name
    )


def verify_totp(secret: str, code: str) -> bool:
    # valid_window=1 tolerates ~30s clock drift on either side.
    return pyotp.TOTP(secret).verify(code, valid_window=1)
