"""Onboarding schemas: Responsible Person & US Agent (spec FR-03, FR-12)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UsAgentType


# ── Responsible Person ───────────────────────────────────────
class ResponsiblePersonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    us_contact: str | None = Field(default=None, max_length=512)


class ResponsiblePersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    us_contact: str | None = Field(default=None, max_length=512)


class ResponsiblePersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    us_contact: str | None
    created_at: datetime


# ── US Agent ─────────────────────────────────────────────────
class UsAgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=512)
    phone: str | None = Field(default=None, max_length=64)
    type: UsAgentType = UsAgentType.direct


class UsAgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=512)
    phone: str | None = Field(default=None, max_length=64)
    type: UsAgentType | None = None


class UsAgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    address: str | None
    phone: str | None
    type: UsAgentType
    created_at: datetime
