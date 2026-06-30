"""Compliance calendar schemas (spec FR-09)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ComplianceTaskStatus, ComplianceTaskType


class ComplianceTaskCreate(BaseModel):
    type: ComplianceTaskType
    # Either give the triggering event date (due date computed via §7.1 rules),
    # or an explicit due_date which takes precedence.
    event_date: date | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None


class ComplianceTaskUpdate(BaseModel):
    assignee_id: uuid.UUID | None = None
    done: bool | None = None


class ComplianceTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    type: ComplianceTaskType
    due_date: date
    status: ComplianceTaskStatus
    assignee_id: uuid.UUID | None
    source_ref: str | None
    days_remaining: int = Field(
        description="오늘 기준 마감까지 남은 일수 (음수면 초과)"
    )
    created_at: datetime
