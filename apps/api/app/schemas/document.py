"""Document vault schemas (spec FR-11)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentType


class DocumentCreate(BaseModel):
    # Polymorphic owner reference, e.g. "product:<uuid>" or "facility:<uuid>".
    owner_ref: str = Field(min_length=1, max_length=128)
    type: DocumentType = DocumentType.other
    file_url: str = Field(min_length=1, max_length=1024)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    owner_ref: str
    type: DocumentType
    file_url: str
    version: int
    created_at: datetime
