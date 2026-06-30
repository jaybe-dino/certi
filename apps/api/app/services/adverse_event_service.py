"""Adverse event (SAE) intake + reporting deadline orchestration (FR-10)."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import AdverseEvent, ComplianceTask
from app.models.enums import (
    AdverseEventSeverity,
    AdverseEventStatus,
    ComplianceTaskType,
)
from app.models.organization import Workspace
from app.models.product import Product
from app.schemas.adverse_event import SeverityCriterion, SeverityGuide
from app.services import deadline_engine

SEVERITY_GUIDE = SeverityGuide(
    report_window_business_days=deadline_engine.SAE_REPORT_BUSINESS_DAYS,
    criteria=[
        SeverityCriterion(
            label="사망 / 생명 위협",
            serious=True,
            examples=["사망", "생명을 위협하는 반응"],
        ),
        SeverityCriterion(
            label="입원 / 입원 연장",
            serious=True,
            examples=["입원 치료 필요", "기존 입원 기간 연장"],
        ),
        SeverityCriterion(
            label="지속적·중대한 장애 / 선천적 이상",
            serious=True,
            examples=["영구적 손상", "기능 장애", "태아 기형"],
        ),
        SeverityCriterion(
            label="중대한 외형 손상 / 감염",
            serious=True,
            examples=["심각한 탈모", "지속성 발진", "심각한 흉터", "감염"],
        ),
        SeverityCriterion(
            label="경미한 자극 / 일시적 반응",
            serious=False,
            examples=["일시적 가려움", "경미한 홍반"],
        ),
    ],
    note=(
        "심각한 유해사례(serious adverse event)는 접수일로부터 15영업일 내 FDA에 "
        "보고해야 합니다. 본 가이드는 참고용이며 최종 심각성 판정은 전문가 검토가 필요합니다."
    ),
)


def report_due_date(event: AdverseEvent) -> date | None:
    """Compute the +15 business-day FDA report deadline for serious events."""
    if event.severity != AdverseEventSeverity.serious or event.reported_at is None:
        return None
    return deadline_engine.compute_due_date(
        ComplianceTaskType.sae_report, event.reported_at.date()
    )


async def get_product_owned(
    db: AsyncSession, product_id: uuid.UUID, org_id: uuid.UUID
) -> Product | None:
    result = await db.execute(
        select(Product)
        .join(Workspace, Product.workspace_id == Workspace.id)
        .where(Product.id == product_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    product: Product,
    severity: AdverseEventSeverity,
    description: str | None,
    reported_at: datetime | None,
) -> AdverseEvent:
    when = reported_at or datetime.now(UTC)
    is_serious = severity == AdverseEventSeverity.serious
    event = AdverseEvent(
        product_id=product.id,
        description=description,
        severity=severity,
        reported_at=when,
        report_status=(
            AdverseEventStatus.reportable if is_serious else AdverseEventStatus.received
        ),
    )
    db.add(event)
    await db.flush()  # assign event.id

    # Serious events generate a +15 business-day SAE reporting task (§7.1).
    if is_serious:
        due = deadline_engine.compute_due_date(
            ComplianceTaskType.sae_report, when.date()
        )
        db.add(
            ComplianceTask(
                workspace_id=product.workspace_id,
                type=ComplianceTaskType.sae_report,
                due_date=due,
                source_ref=f"adverse_event:{event.id}",
                status=deadline_engine.compute_status(due, date.today()),
            )
        )

    await db.commit()
    await db.refresh(event)
    return event


async def list_for_product(db: AsyncSession, product_id: uuid.UUID) -> list[AdverseEvent]:
    result = await db.execute(
        select(AdverseEvent)
        .where(AdverseEvent.product_id == product_id)
        .order_by(AdverseEvent.reported_at.desc())
    )
    return list(result.scalars().all())


async def get_owned(
    db: AsyncSession, event_id: uuid.UUID, org_id: uuid.UUID
) -> AdverseEvent | None:
    result = await db.execute(
        select(AdverseEvent)
        .join(Product, AdverseEvent.product_id == Product.id)
        .join(Workspace, Product.workspace_id == Workspace.id)
        .where(AdverseEvent.id == event_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


async def update(db: AsyncSession, event: AdverseEvent, data: dict) -> AdverseEvent:
    for key, value in data.items():
        setattr(event, key, value)
    await db.commit()
    await db.refresh(event)
    return event
