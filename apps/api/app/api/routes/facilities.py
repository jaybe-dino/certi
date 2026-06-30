"""Facility registration endpoints (spec FR-04)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.organization import User
from app.schemas.facility import (
    FacilityCreate,
    FacilityRead,
    FacilityUpdate,
    GenerateSplResponse,
    MarkRegisteredResponse,
    SubmissionRead,
    ValidationResult,
)
from app.services import facility_service, workspace_service

router = APIRouter(tags=["facilities"])


async def _require_workspace(db, workspace_id: uuid.UUID, user: User):
    ws = await workspace_service.get_owned(db, workspace_id, user.org_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


async def _require_facility(db, facility_id: uuid.UUID, user: User):
    facility = await facility_service.get_owned(db, facility_id, user.org_id)
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    return facility


@router.post(
    "/workspaces/{workspace_id}/facilities",
    response_model=FacilityRead,
    status_code=status.HTTP_201_CREATED,
    summary="시설 생성 (위저드 저장)",
)
async def create_facility(
    workspace_id: uuid.UUID,
    payload: FacilityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await _require_workspace(db, workspace_id, current_user)
    return await facility_service.create(db, workspace=ws, data=payload.model_dump())


@router.get(
    "/workspaces/{workspace_id}/facilities",
    response_model=list[FacilityRead],
    summary="시설 목록",
)
async def list_facilities(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_workspace(db, workspace_id, current_user)
    return await facility_service.list_for_workspace(db, workspace_id)


@router.get(
    "/facilities/{facility_id}",
    response_model=FacilityRead,
    summary="시설 단건 조회",
)
async def get_facility(
    facility_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _require_facility(db, facility_id, current_user)


@router.patch(
    "/facilities/{facility_id}",
    response_model=FacilityRead,
    summary="시설 수정",
)
async def update_facility(
    facility_id: uuid.UUID,
    payload: FacilityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facility = await _require_facility(db, facility_id, current_user)
    data = payload.model_dump(exclude_unset=True)
    return await facility_service.update(db, facility, data)


@router.get(
    "/facilities/{facility_id}/validate",
    response_model=ValidationResult,
    summary="제출 전 검증 (§7.3)",
)
async def validate_facility(
    facility_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facility = await _require_facility(db, facility_id, current_user)
    errors = facility_service.validate(facility)
    return ValidationResult(valid=not errors, errors=errors)


@router.post(
    "/facilities/{facility_id}/generate-spl",
    response_model=GenerateSplResponse,
    summary="SPL 생성 + 제출 레코드 생성 (Form 5066)",
)
async def generate_spl(
    facility_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facility = await _require_facility(db, facility_id, current_user)
    submission, errors = await facility_service.generate_spl_submission(db, facility)
    if errors:
        raise HTTPException(
            status_code=422,  # Unprocessable Content
            detail={"message": "Validation failed", "errors": errors},
        )
    return GenerateSplResponse(
        submission=SubmissionRead.model_validate(submission),
        facility=FacilityRead.model_validate(facility),
    )


@router.post(
    "/facilities/{facility_id}/mark-registered",
    response_model=MarkRegisteredResponse,
    summary="시설 등록 완료 처리 (+2년 갱신 태스크 자동 생성, §7.1)",
)
async def mark_registered(
    facility_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    facility = await _require_facility(db, facility_id, current_user)
    facility, renewal = await facility_service.mark_registered(db, facility)
    return MarkRegisteredResponse(
        facility=FacilityRead.model_validate(facility),
        renewal_task_id=renewal.id,
        renewal_due_date=renewal.due_date,
    )
