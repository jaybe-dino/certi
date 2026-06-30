"""Document vault persistence with auto-versioning (spec FR-11)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.enums import DocumentType


async def create(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    owner_ref: str,
    doc_type: DocumentType,
    file_url: str,
) -> Document:
    """Create a document; version auto-increments per (owner_ref, type)."""
    max_version = await db.scalar(
        select(func.max(Document.version)).where(
            Document.workspace_id == workspace_id,
            Document.owner_ref == owner_ref,
            Document.type == doc_type,
        )
    )
    document = Document(
        workspace_id=workspace_id,
        owner_ref=owner_ref,
        type=doc_type,
        file_url=file_url,
        version=(max_version or 0) + 1,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def list_for_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    owner_ref: str | None = None,
    doc_type: DocumentType | None = None,
) -> list[Document]:
    stmt = select(Document).where(Document.workspace_id == workspace_id)
    if owner_ref is not None:
        stmt = stmt.where(Document.owner_ref == owner_ref)
    if doc_type is not None:
        stmt = stmt.where(Document.type == doc_type)
    stmt = stmt.order_by(Document.owner_ref, Document.type, Document.version)
    result = await db.execute(stmt)
    return list(result.scalars().all())
