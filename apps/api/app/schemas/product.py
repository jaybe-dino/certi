"""Product, ingredient (INCI), and bulk-upload schemas (FR-05, FR-06, FR-07)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InciConfidence


# ── Product ──────────────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=128)
    label_url: str | None = Field(default=None, max_length=1024)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=128)
    label_url: str | None = Field(default=None, max_length=1024)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    category: str | None
    label_url: str | None
    status: str
    created_at: datetime


# ── Ingredient / INCI ────────────────────────────────────────
class IngredientCreate(BaseModel):
    raw_name: str = Field(min_length=1, max_length=255)
    # Optional manual override; if absent the INCI engine fills it.
    inci_name: str | None = Field(default=None, max_length=255)


class IngredientUpdate(BaseModel):
    inci_name: str | None = Field(default=None, max_length=255)
    flag: bool | None = None


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    raw_name: str
    inci_name: str | None
    confidence: InciConfidence | None
    flag: bool


class IngredientBulkCreate(BaseModel):
    raw_names: list[str] = Field(min_length=1)


# ── Facility linking ─────────────────────────────────────────
class ProductFacilityLink(BaseModel):
    facility_id: uuid.UUID


# ── Bulk product upload (FR-06) ──────────────────────────────
class BulkRowResult(BaseModel):
    row: int
    product_id: uuid.UUID | None = None
    errors: list[str] = Field(default_factory=list)


class BulkUploadResponse(BaseModel):
    created: int
    failed: int
    results: list[BulkRowResult]
