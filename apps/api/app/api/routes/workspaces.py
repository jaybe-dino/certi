"""Workspace endpoints (multi-brand support, spec FR-14 subset)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.organization import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post(
    "",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
    summary="워크스페이스(브랜드) 생성",
)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await workspace_service.create(
        db, org_id=current_user.org_id, brand_name=payload.brand_name
    )


@router.get("", response_model=list[WorkspaceRead], summary="워크스페이스 목록")
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await workspace_service.list_for_org(db, current_user.org_id)
