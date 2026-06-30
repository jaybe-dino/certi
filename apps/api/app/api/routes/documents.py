"""Document vault endpoints (spec FR-11)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_path_workspace
from app.core.database import get_db
from app.models.enums import DocumentType
from app.models.organization import User, Workspace
from app.schemas.document import DocumentCreate, DocumentRead
from app.services import audit_service, document_service

router = APIRouter(tags=["documents"])


@router.post(
    "/workspaces/{workspace_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="문서 보관 (자동 버전 증가)",
)
async def create_document(
    payload: DocumentCreate,
    workspace: Workspace = Depends(get_path_workspace),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await document_service.create(
        db,
        workspace_id=workspace.id,
        owner_ref=payload.owner_ref,
        doc_type=payload.type,
        file_url=payload.file_url,
    )
    await audit_service.record(
        db,
        actor_id=current_user.id,
        workspace_id=workspace.id,
        action="document.create",
        target=f"document:{document.id}",
        payload={"owner_ref": document.owner_ref, "type": document.type.value},
    )
    return document


@router.get(
    "/workspaces/{workspace_id}/documents",
    response_model=list[DocumentRead],
    summary="문서 목록 (owner_ref / type 필터)",
)
async def list_documents(
    owner_ref: str | None = None,
    type: DocumentType | None = None,
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await document_service.list_for_workspace(
        db, workspace.id, owner_ref=owner_ref, doc_type=type
    )
