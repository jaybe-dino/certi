"""Liveness / readiness probes."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Process is up. Does not touch dependencies."""
    return {"status": "ok", "environment": settings.environment}


@router.get("/health/ready", summary="Readiness probe")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Verifies the database connection is reachable."""
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
