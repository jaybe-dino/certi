"""Facility schemas (spec FR-04)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import FacilityStatus, SubmissionStatus, SubmissionType


class FacilityCreate(BaseModel):
    name_en: str = Field(min_length=1, max_length=255)
    address_en: str | None = Field(default=None, max_length=512)
    email: EmailStr | None = None
    fei: str | None = Field(default=None, max_length=32)


class FacilityUpdate(BaseModel):
    name_en: str | None = Field(default=None, min_length=1, max_length=255)
    address_en: str | None = Field(default=None, max_length=512)
    email: EmailStr | None = None
    fei: str | None = Field(default=None, max_length=32)


class FacilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name_en: str
    address_en: str | None
    email: str | None
    fei: str | None
    status: FacilityStatus
    created_at: datetime
    updated_at: datetime


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str]


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: SubmissionType
    status: SubmissionStatus
    esg_id: str | None
    spl_xml: str | None


class GenerateSplResponse(BaseModel):
    submission: SubmissionRead
    # Present for facility (5066) submissions; null for product (5067) listings.
    facility: FacilityRead | None = None


class MarkRegisteredResponse(BaseModel):
    facility: FacilityRead
    renewal_task_id: uuid.UUID
    renewal_due_date: date
