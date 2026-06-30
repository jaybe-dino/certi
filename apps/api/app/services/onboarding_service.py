"""Responsible Person & US Agent persistence (spec FR-03, FR-12)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facility import ResponsiblePerson, UsAgent
from app.models.organization import Workspace


# ── Responsible Person ───────────────────────────────────────
async def create_rp(
    db: AsyncSession, *, workspace_id: uuid.UUID, data: dict
) -> ResponsiblePerson:
    rp = ResponsiblePerson(workspace_id=workspace_id, **data)
    db.add(rp)
    await db.commit()
    await db.refresh(rp)
    return rp


async def list_rp(db: AsyncSession, workspace_id: uuid.UUID) -> list[ResponsiblePerson]:
    result = await db.execute(
        select(ResponsiblePerson)
        .where(ResponsiblePerson.workspace_id == workspace_id)
        .order_by(ResponsiblePerson.created_at)
    )
    return list(result.scalars().all())


async def get_rp_owned(
    db: AsyncSession, rp_id: uuid.UUID, org_id: uuid.UUID
) -> ResponsiblePerson | None:
    result = await db.execute(
        select(ResponsiblePerson)
        .join(Workspace, ResponsiblePerson.workspace_id == Workspace.id)
        .where(ResponsiblePerson.id == rp_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


# ── US Agent ─────────────────────────────────────────────────
async def create_agent(
    db: AsyncSession, *, workspace_id: uuid.UUID, data: dict
) -> UsAgent:
    agent = UsAgent(workspace_id=workspace_id, **data)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def list_agents(db: AsyncSession, workspace_id: uuid.UUID) -> list[UsAgent]:
    result = await db.execute(
        select(UsAgent)
        .where(UsAgent.workspace_id == workspace_id)
        .order_by(UsAgent.created_at)
    )
    return list(result.scalars().all())


async def get_agent_owned(
    db: AsyncSession, agent_id: uuid.UUID, org_id: uuid.UUID
) -> UsAgent | None:
    result = await db.execute(
        select(UsAgent)
        .join(Workspace, UsAgent.workspace_id == Workspace.id)
        .where(UsAgent.id == agent_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


async def update_entity(db: AsyncSession, entity, data: dict):
    for key, value in data.items():
        setattr(entity, key, value)
    await db.commit()
    await db.refresh(entity)
    return entity
