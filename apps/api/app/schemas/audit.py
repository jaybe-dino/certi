"""Audit log schemas (spec FR-17)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    workspace_id: uuid.UUID | None
    action: str
    target: str | None
    payload: dict | None
    created_at: datetime
