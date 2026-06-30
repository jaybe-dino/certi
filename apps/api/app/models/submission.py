"""Submission entity — SPL generation + FDA ESG tracking (spec §5.1, §6.1)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import SubmissionStatus, SubmissionType


class Submission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "submission"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    # A submission targets either a facility (5066) or a product (5067).
    facility_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facility.id", ondelete="SET NULL")
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product.id", ondelete="SET NULL")
    )

    type: Mapped[SubmissionType] = mapped_column(
        Enum(SubmissionType, name="submission_type"), nullable=False
    )
    spl_xml: Mapped[str | None] = mapped_column(Text)
    esg_id: Mapped[str | None] = mapped_column(index=True)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        default=SubmissionStatus.generated,
        nullable=False,
    )
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
