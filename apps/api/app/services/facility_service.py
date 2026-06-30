"""Facility persistence + SPL submission orchestration (spec FR-04)."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import ComplianceTask
from app.models.enums import (
    ComplianceTaskType,
    FacilityStatus,
    SubmissionStatus,
    SubmissionType,
)
from app.models.facility import Facility
from app.models.organization import Workspace
from app.models.submission import Submission
from app.services import deadline_engine, spl_service, validation_service


async def create(
    db: AsyncSession, *, workspace: Workspace, data: dict
) -> Facility:
    facility = Facility(workspace_id=workspace.id, **data)
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    return facility


async def list_for_workspace(
    db: AsyncSession, workspace_id: uuid.UUID
) -> list[Facility]:
    result = await db.execute(
        select(Facility)
        .where(Facility.workspace_id == workspace_id)
        .order_by(Facility.created_at)
    )
    return list(result.scalars().all())


async def get_owned(
    db: AsyncSession, facility_id: uuid.UUID, org_id: uuid.UUID
) -> Facility | None:
    """Fetch a facility only if its workspace belongs to ``org_id``."""
    result = await db.execute(
        select(Facility)
        .join(Workspace, Facility.workspace_id == Workspace.id)
        .where(Facility.id == facility_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


async def update(db: AsyncSession, facility: Facility, data: dict) -> Facility:
    for key, value in data.items():
        setattr(facility, key, value)
    await db.commit()
    await db.refresh(facility)
    return facility


def validate(facility: Facility) -> list[str]:
    return validation_service.validate_facility_for_submission(facility)


async def generate_spl_submission(
    db: AsyncSession, facility: Facility
) -> tuple[Submission | None, list[str]]:
    """Validate, generate SPL, and persist a submission record.

    Returns (submission, errors). On validation failure returns (None, errors)
    and leaves the facility untouched.
    """
    errors = validate(facility)
    if errors:
        return None, errors

    spl_xml = spl_service.generate_facility_spl(facility)
    submission = Submission(
        workspace_id=facility.workspace_id,
        facility_id=facility.id,
        type=SubmissionType.facility,
        spl_xml=spl_xml,
        status=SubmissionStatus.generated,
    )
    # Facility moves to "submitting" once an SPL has been generated for review.
    facility.status = FacilityStatus.submitting
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    await db.refresh(facility)
    return submission, []


async def mark_registered(
    db: AsyncSession, facility: Facility
) -> tuple[Facility, ComplianceTask]:
    """Mark a facility registered and auto-create its +2y renewal task (§7.1)."""
    facility.status = FacilityStatus.registered
    today = date.today()
    renewal_due = deadline_engine.compute_due_date(
        ComplianceTaskType.facility_renewal, today
    )
    renewal = ComplianceTask(
        workspace_id=facility.workspace_id,
        type=ComplianceTaskType.facility_renewal,
        due_date=renewal_due,
        source_ref=f"facility:{facility.id}",
        status=deadline_engine.compute_status(renewal_due, today),
    )
    db.add(renewal)
    await db.commit()
    await db.refresh(facility)
    await db.refresh(renewal)
    return facility, renewal
