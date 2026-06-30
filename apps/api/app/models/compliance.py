"""Compliance calendar and adverse-event entities (spec §5.1, §7.1)."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import (
    AdverseEventSeverity,
    AdverseEventStatus,
    ComplianceTaskStatus,
    ComplianceTaskType,
)


class ComplianceTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_task"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[ComplianceTaskType] = mapped_column(
        Enum(ComplianceTaskType, name="compliance_task_type"), nullable=False
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    status: Mapped[ComplianceTaskStatus] = mapped_column(
        Enum(ComplianceTaskStatus, name="compliance_task_status"),
        default=ComplianceTaskStatus.scheduled,
        nullable=False,
    )
    # Optional back-reference to what generated this task (facility/product/submission).
    source_ref: Mapped[str | None] = mapped_column()


class AdverseEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "adverse_event"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    severity: Mapped[AdverseEventSeverity] = mapped_column(
        Enum(AdverseEventSeverity, name="adverse_event_severity"), nullable=False
    )
    report_status: Mapped[AdverseEventStatus] = mapped_column(
        Enum(AdverseEventStatus, name="adverse_event_status"),
        default=AdverseEventStatus.received,
        nullable=False,
    )
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
