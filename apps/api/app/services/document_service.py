"""Document vault persistence with auto-versioning (spec FR-11)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.enums import DocumentType
from app.schemas.document import IntakeChecklist, IntakeChecklistItem

# Company-level intake documents an agency collects (spec docs/AGENT_MODEL.md §1).
# Product-level docs (product_brief, ingredient_sheet) are tracked per product.
REQUIRED_INTAKE_DOCS: list[tuple[DocumentType, str, bool]] = [
    (DocumentType.biz_registration, "영문 사업자등록증", True),
    (DocumentType.factory_registration, "영문 공장등록증", True),
    (DocumentType.business_card, "대표/담당자 명함", True),
]


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


async def intake_checklist(db: AsyncSession, workspace_id: uuid.UUID) -> IntakeChecklist:
    """Company-level intake-document checklist with per-type upload status."""
    # Latest file_url per document type in this workspace.
    result = await db.execute(
        select(Document.type, Document.file_url, Document.version)
        .where(Document.workspace_id == workspace_id)
        .order_by(Document.type, Document.version.desc())
    )
    latest: dict[DocumentType, str] = {}
    for doc_type, file_url, _version in result.all():
        latest.setdefault(doc_type, file_url)

    items: list[IntakeChecklistItem] = []
    complete = True
    for doc_type, title, required in REQUIRED_INTAKE_DOCS:
        uploaded = doc_type in latest
        if required and not uploaded:
            complete = False
        items.append(
            IntakeChecklistItem(
                type=doc_type,
                title=title,
                required=required,
                uploaded=uploaded,
                latest_file_url=latest.get(doc_type),
            )
        )
    return IntakeChecklist(complete=complete, items=items)
