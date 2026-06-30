"""Workspace persistence, scoped to an organization."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Workspace


async def create(db: AsyncSession, *, org_id: uuid.UUID, brand_name: str) -> Workspace:
    ws = Workspace(org_id=org_id, brand_name=brand_name)
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return ws


async def list_for_org(db: AsyncSession, org_id: uuid.UUID) -> list[Workspace]:
    result = await db.execute(
        select(Workspace).where(Workspace.org_id == org_id).order_by(Workspace.created_at)
    )
    return list(result.scalars().all())


async def get_owned(
    db: AsyncSession, workspace_id: uuid.UUID, org_id: uuid.UUID
) -> Workspace | None:
    """Fetch a workspace only if it belongs to ``org_id`` (tenant isolation)."""
    ws = await db.get(Workspace, workspace_id)
    if ws is None or ws.org_id != org_id:
        return None
    return ws
