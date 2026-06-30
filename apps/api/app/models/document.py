"""Document vault and append-only audit log (spec §5.1, §9)."""

import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import DocumentType


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    # Polymorphic owner reference, e.g. "product:<uuid>" / "facility:<uuid>".
    owner_ref: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"), default=DocumentType.other, nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Append-only — never updated or deleted (spec §9 audit requirement)."""

    __tablename__ = "audit_log"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL")
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict | None] = mapped_column(JSONB)
