"""User & organization persistence and authentication logic (spec FR-02)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.enums import PlanTier, UserRole
from app.models.organization import Organization, User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def register(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None,
    company_name: str,
) -> User:
    """Create a new organization and its owner user in one transaction."""
    org = Organization(name=company_name, plan=PlanTier.free)
    db.add(org)
    await db.flush()  # assign org.id

    user = User(
        org_id=org.id,
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        role=UserRole.owner,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
