"""Adverse event (SAE) schemas (spec FR-10)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AdverseEventSeverity, AdverseEventStatus


class AdverseEventCreate(BaseModel):
    product_id: uuid.UUID
    severity: AdverseEventSeverity
    description: str | None = Field(default=None, max_length=4000)
    # Defaults to now on the server when omitted.
    reported_at: datetime | None = None


class AdverseEventUpdate(BaseModel):
    report_status: AdverseEventStatus | None = None
    description: str | None = Field(default=None, max_length=4000)


class AdverseEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    description: str | None
    severity: AdverseEventSeverity
    report_status: AdverseEventStatus
    reported_at: datetime | None
    # Set only for serious events: FDA report deadline (+15 business days).
    report_due_date: date | None = None


class SeverityCriterion(BaseModel):
    label: str
    serious: bool
    examples: list[str]


class SeverityGuide(BaseModel):
    report_window_business_days: int
    criteria: list[SeverityCriterion]
    note: str
