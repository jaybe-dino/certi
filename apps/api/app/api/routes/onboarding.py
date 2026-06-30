"""Onboarding endpoints: Responsible Person & US Agent (spec FR-03, FR-12)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_path_workspace
from app.core.database import get_db
from app.models.organization import User, Workspace
from app.schemas.onboarding import (
    ResponsiblePersonCreate,
    ResponsiblePersonRead,
    ResponsiblePersonUpdate,
    UsAgentCreate,
    UsAgentRead,
    UsAgentUpdate,
)
from app.services import onboarding_service

router = APIRouter(tags=["onboarding"])


# ── Responsible Person ───────────────────────────────────────
@router.post(
    "/workspaces/{workspace_id}/responsible-persons",
    response_model=ResponsiblePersonRead,
    status_code=status.HTTP_201_CREATED,
    summary="책임자(RP) 등록",
)
async def create_rp(
    payload: ResponsiblePersonCreate,
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await onboarding_service.create_rp(
        db, workspace_id=workspace.id, data=payload.model_dump()
    )


@router.get(
    "/workspaces/{workspace_id}/responsible-persons",
    response_model=list[ResponsiblePersonRead],
    summary="책임자 목록",
)
async def list_rp(
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await onboarding_service.list_rp(db, workspace.id)


@router.patch(
    "/responsible-persons/{rp_id}",
    response_model=ResponsiblePersonRead,
    summary="책임자 수정",
)
async def update_rp(
    rp_id: uuid.UUID,
    payload: ResponsiblePersonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rp = await onboarding_service.get_rp_owned(db, rp_id, current_user.org_id)
    if rp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RP not found")
    return await onboarding_service.update_entity(
        db, rp, payload.model_dump(exclude_unset=True)
    )


# ── US Agent ─────────────────────────────────────────────────
@router.post(
    "/workspaces/{workspace_id}/us-agents",
    response_model=UsAgentRead,
    status_code=status.HTTP_201_CREATED,
    summary="US Agent 등록",
)
async def create_agent(
    payload: UsAgentCreate,
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await onboarding_service.create_agent(
        db, workspace_id=workspace.id, data=payload.model_dump()
    )


@router.get(
    "/workspaces/{workspace_id}/us-agents",
    response_model=list[UsAgentRead],
    summary="US Agent 목록",
)
async def list_agents(
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await onboarding_service.list_agents(db, workspace.id)


@router.patch(
    "/us-agents/{agent_id}",
    response_model=UsAgentRead,
    summary="US Agent 수정",
)
async def update_agent(
    agent_id: uuid.UUID,
    payload: UsAgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await onboarding_service.get_agent_owned(db, agent_id, current_user.org_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="US Agent not found"
        )
    return await onboarding_service.update_entity(
        db, agent, payload.model_dump(exclude_unset=True)
    )
