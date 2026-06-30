"""Facility, responsible person, and US agent entities (spec §5.1)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import FacilityStatus, UsAgentType

if TYPE_CHECKING:
    from app.models.product import Product


class Facility(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "facility"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    address_en: Mapped[str | None] = mapped_column(String(512))
    email: Mapped[str | None] = mapped_column(String(320))
    fei: Mapped[str | None] = mapped_column(String(32), index=True)
    status: Mapped[FacilityStatus] = mapped_column(
        Enum(FacilityStatus, name="facility_status"),
        default=FacilityStatus.draft,
        nullable=False,
    )

    product_links: Mapped[list["ProductFacility"]] = relationship(
        back_populates="facility", cascade="all, delete-orphan"
    )


class ResponsiblePerson(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "responsible_person"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    us_contact: Mapped[str | None] = mapped_column(String(512))


class UsAgent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "us_agent"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(512))
    phone: Mapped[str | None] = mapped_column(String(64))
    type: Mapped[UsAgentType] = mapped_column(
        Enum(UsAgentType, name="us_agent_type"),
        default=UsAgentType.direct,
        nullable=False,
    )


class ProductFacility(Base):
    """Association table for the product ↔ facility M:N relation (spec §5.1)."""

    __tablename__ = "product_facility"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id", ondelete="CASCADE"),
        primary_key=True,
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facility.id", ondelete="CASCADE"),
        primary_key=True,
    )

    facility: Mapped["Facility"] = relationship(back_populates="product_links")
    product: Mapped["Product"] = relationship(back_populates="facility_links")
