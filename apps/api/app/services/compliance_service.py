"""Compliance task persistence + deadline orchestration (spec FR-09)."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import ComplianceTask
from app.models.enums import ComplianceTaskStatus, ComplianceTaskType
from app.models.organization import Workspace
from app.services import deadline_engine


async def create_task(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    task_type: ComplianceTaskType,
    event_date: date | None = None,
    due_date: date | None = None,
    assignee_id: uuid.UUID | None = None,
    source_ref: str | None = None,
) -> ComplianceTask:
    """Create a task. ``due_date`` wins; otherwise it is derived from
    ``event_date`` via the §7.1 rules."""
    if due_date is None:
        if event_date is None:
            raise ValueError("event_date or due_date is required")
        due_date = deadline_engine.compute_due_date(task_type, event_date)

    task = ComplianceTask(
        workspace_id=workspace_id,
        type=task_type,
        due_date=due_date,
        assignee_id=assignee_id,
        source_ref=source_ref,
        status=deadline_engine.compute_status(due_date, date.today()),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


def _refresh_status(task: ComplianceTask, today: date) -> None:
    """Recompute the live status in place (keeps 'done' sticky)."""
    if task.status == ComplianceTaskStatus.done:
        return
    task.status = deadline_engine.compute_status(task.due_date, today)


async def list_for_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    status_filter: ComplianceTaskStatus | None = None,
) -> list[ComplianceTask]:
    result = await db.execute(
        select(ComplianceTask)
        .where(ComplianceTask.workspace_id == workspace_id)
        .order_by(ComplianceTask.due_date)
    )
    tasks = list(result.scalars().all())

    today = date.today()
    changed = False
    for task in tasks:
        before = task.status
        _refresh_status(task, today)
        changed = changed or task.status != before
    if changed:
        await db.commit()

    if status_filter is not None:
        tasks = [t for t in tasks if t.status == status_filter]
    return tasks


async def get_owned(
    db: AsyncSession, task_id: uuid.UUID, org_id: uuid.UUID
) -> ComplianceTask | None:
    result = await db.execute(
        select(ComplianceTask)
        .join(Workspace, ComplianceTask.workspace_id == Workspace.id)
        .where(ComplianceTask.id == task_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


async def update_task(
    db: AsyncSession,
    task: ComplianceTask,
    *,
    assignee_id: uuid.UUID | None = None,
    done: bool | None = None,
) -> ComplianceTask:
    if assignee_id is not None:
        task.assignee_id = assignee_id
    if done is True:
        task.status = ComplianceTaskStatus.done
    elif done is False:
        _refresh_status_force(task)
    await db.commit()
    await db.refresh(task)
    return task


def _refresh_status_force(task: ComplianceTask) -> None:
    task.status = deadline_engine.compute_status(task.due_date, date.today())


def days_remaining(task: ComplianceTask) -> int:
    return (task.due_date - date.today()).days
