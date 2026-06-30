"""Audit log query endpoints (spec FR-17). Read-only; the log is append-only."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_path_workspace
from app.core.database import get_db
from app.models.organization import Workspace
from app.schemas.audit import AuditLogRead
from app.services import audit_service

router = APIRouter(tags=["audit"])


@router.get(
    "/workspaces/{workspace_id}/audit-logs",
    response_model=list[AuditLogRead],
    summary="감사 로그 조회 (실사 대비)",
)
async def list_audit_logs(
    action: str | None = None,
    limit: int = Query(default=100, le=500),
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await audit_service.list_for_workspace(
        db, workspace.id, action=action, limit=limit
    )
