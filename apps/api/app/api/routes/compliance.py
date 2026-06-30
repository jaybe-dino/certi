"""Compliance calendar endpoints (spec FR-09)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.compliance import ComplianceTask
from app.models.enums import ComplianceTaskStatus
from app.models.organization import User
from app.schemas.compliance import (
    ComplianceTaskCreate,
    ComplianceTaskRead,
    ComplianceTaskUpdate,
)
from app.services import compliance_service, workspace_service

router = APIRouter(tags=["compliance"])


def _to_read(task: ComplianceTask) -> ComplianceTaskRead:
    return ComplianceTaskRead(
        id=task.id,
        workspace_id=task.workspace_id,
        type=task.type,
        due_date=task.due_date,
        status=task.status,
        assignee_id=task.assignee_id,
        source_ref=task.source_ref,
        days_remaining=compliance_service.days_remaining(task),
        created_at=task.created_at,
    )


async def _require_workspace(db, workspace_id: uuid.UUID, user: User):
    ws = await workspace_service.get_owned(db, workspace_id, user.org_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


@router.post(
    "/workspaces/{workspace_id}/compliance-tasks",
    response_model=ComplianceTaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="컴플라이언스 태스크 생성 (이벤트일 → 마감 자동 산출)",
)
async def create_task(
    workspace_id: uuid.UUID,
    payload: ComplianceTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_workspace(db, workspace_id, current_user)
    if payload.event_date is None and payload.due_date is None:
        raise HTTPException(
            status_code=422,
            detail="event_date 또는 due_date 중 하나는 필요합니다.",
        )
    task = await compliance_service.create_task(
        db,
        workspace_id=workspace_id,
        task_type=payload.type,
        event_date=payload.event_date,
        due_date=payload.due_date,
        assignee_id=payload.assignee_id,
    )
    return _to_read(task)


@router.get(
    "/workspaces/{workspace_id}/compliance-tasks",
    response_model=list[ComplianceTaskRead],
    summary="컴플라이언스 캘린더 (마감 자동 갱신)",
)
async def list_tasks(
    workspace_id: uuid.UUID,
    status_filter: ComplianceTaskStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_workspace(db, workspace_id, current_user)
    tasks = await compliance_service.list_for_workspace(
        db, workspace_id, status_filter=status_filter
    )
    return [_to_read(t) for t in tasks]


@router.patch(
    "/compliance-tasks/{task_id}",
    response_model=ComplianceTaskRead,
    summary="태스크 수정 (담당자 지정 / 완료 처리)",
)
async def update_task(
    task_id: uuid.UUID,
    payload: ComplianceTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await compliance_service.get_owned(db, task_id, current_user.org_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = await compliance_service.update_task(
        db, task, assignee_id=payload.assignee_id, done=payload.done
    )
    return _to_read(task)
