"""Append-only audit logging (spec FR-17, §9).

Records are never updated or deleted. ``record`` is safe to call after a
primary action has committed; it persists its own row.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import AuditLog


async def record(
    db: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    workspace_id: uuid.UUID | None,
    action: str,
    target: str | None = None,
    payload: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        workspace_id=workspace_id,
        action=action,
        target=target,
        payload=payload,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_for_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    action: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    stmt = select(AuditLog).where(AuditLog.workspace_id == workspace_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
