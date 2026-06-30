"""Adverse event (SAE) endpoints (spec FR-10)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.organization import User
from app.schemas.adverse_event import (
    AdverseEventCreate,
    AdverseEventRead,
    AdverseEventUpdate,
    SeverityGuide,
)
from app.services import adverse_event_service as ae_service

router = APIRouter(tags=["adverse-events"])


def _to_read(event) -> AdverseEventRead:
    read = AdverseEventRead.model_validate(event)
    read.report_due_date = ae_service.report_due_date(event)
    return read


@router.get(
    "/adverse-events/severity-guide",
    response_model=SeverityGuide,
    summary="심각성 판정 가이드",
)
async def severity_guide() -> SeverityGuide:
    return ae_service.SEVERITY_GUIDE


@router.post(
    "/adverse-events",
    response_model=AdverseEventRead,
    status_code=status.HTTP_201_CREATED,
    summary="유해사례 접수 (심각 시 +15영업일 보고 태스크 자동 생성)",
)
async def create_event(
    payload: AdverseEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await ae_service.get_product_owned(
        db, payload.product_id, current_user.org_id
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    event = await ae_service.create(
        db,
        product=product,
        severity=payload.severity,
        description=payload.description,
        reported_at=payload.reported_at,
    )
    return _to_read(event)


@router.get(
    "/products/{product_id}/adverse-events",
    response_model=list[AdverseEventRead],
    summary="제품별 유해사례 목록",
)
async def list_for_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await ae_service.get_product_owned(db, product_id, current_user.org_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    events = await ae_service.list_for_product(db, product_id)
    return [_to_read(e) for e in events]


@router.patch(
    "/adverse-events/{event_id}",
    response_model=AdverseEventRead,
    summary="유해사례 상태 갱신 (제출 연계)",
)
async def update_event(
    event_id: uuid.UUID,
    payload: AdverseEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event = await ae_service.get_owned(db, event_id, current_user.org_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    event = await ae_service.update(db, event, payload.model_dump(exclude_unset=True))
    return _to_read(event)
