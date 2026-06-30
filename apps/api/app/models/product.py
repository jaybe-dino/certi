"""Product and ingredient entities (spec §5.1)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import InciConfidence

if TYPE_CHECKING:
    from app.models.facility import ProductFacility


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128))
    label_url: Mapped[str | None] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)

    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    facility_links: Mapped[list["ProductFacility"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class Ingredient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ingredient"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    raw_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inci_name: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[InciConfidence | None] = mapped_column(
        Enum(InciConfidence, name="inci_confidence")
    )
    flag: Mapped[bool] = mapped_column(default=False, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="ingredients")
