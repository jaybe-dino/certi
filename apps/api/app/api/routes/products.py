"""Product listing, INCI ingredients, facility linking, bulk upload (FR-05/06/07)."""

import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_path_workspace
from app.core.database import get_db
from app.models.organization import User, Workspace
from app.schemas.facility import GenerateSplResponse, SubmissionRead
from app.schemas.product import (
    BulkRowResult,
    BulkUploadResponse,
    IngredientBulkCreate,
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
    ProductCreate,
    ProductFacilityLink,
    ProductRead,
    ProductUpdate,
)
from app.services import audit_service, product_service

router = APIRouter(tags=["products"])


async def _require_product(db, product_id: uuid.UUID, user: User):
    product = await product_service.get_owned(db, product_id, user.org_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# ── Product CRUD ─────────────────────────────────────────────
@router.post(
    "/workspaces/{workspace_id}/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="제품 단건 등록 (Form 5067)",
)
async def create_product(
    payload: ProductCreate,
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.create(db, workspace_id=workspace.id, data=payload.model_dump())


@router.get(
    "/workspaces/{workspace_id}/products",
    response_model=list[ProductRead],
    summary="제품 목록",
)
async def list_products(
    workspace: Workspace = Depends(get_path_workspace),
    db: AsyncSession = Depends(get_db),
):
    return await product_service.list_for_workspace(db, workspace.id)


@router.get("/products/{product_id}", response_model=ProductRead, summary="제품 조회")
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _require_product(db, product_id, current_user)


@router.patch("/products/{product_id}", response_model=ProductRead, summary="제품 수정")
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _require_product(db, product_id, current_user)
    return await product_service.update(db, product, payload.model_dump(exclude_unset=True))


# ── Facility linking ─────────────────────────────────────────
@router.post(
    "/products/{product_id}/facilities",
    response_model=ProductRead,
    summary="제품-시설(FEI) 연동",
)
async def link_facility(
    product_id: uuid.UUID,
    payload: ProductFacilityLink,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _require_product(db, product_id, current_user)
    ok = await product_service.link_facility(db, product=product, facility_id=payload.facility_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="동일 워크스페이스의 유효한 시설이 아닙니다.",
        )
    return product


# ── Ingredients / INCI (FR-07) ───────────────────────────────
@router.post(
    "/products/{product_id}/ingredients",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    summary="성분 추가 (INCI 자동 매핑)",
)
async def add_ingredient(
    product_id: uuid.UUID,
    payload: IngredientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _require_product(db, product_id, current_user)
    return await product_service.add_ingredient(
        db, product_id=product.id, raw_name=payload.raw_name, inci_name=payload.inci_name
    )


@router.post(
    "/products/{product_id}/ingredients/bulk",
    response_model=list[IngredientRead],
    summary="성분 일괄 추가 (INCI 자동 매핑)",
)
async def add_ingredients_bulk(
    product_id: uuid.UUID,
    payload: IngredientBulkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _require_product(db, product_id, current_user)
    return await product_service.add_ingredients_bulk(
        db, product_id=product.id, raw_names=payload.raw_names
    )


@router.get(
    "/products/{product_id}/ingredients",
    response_model=list[IngredientRead],
    summary="성분 목록",
)
async def list_ingredients(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _require_product(db, product_id, current_user)
    return await product_service.list_ingredients(db, product.id)


@router.patch(
    "/ingredients/{ingredient_id}",
    response_model=IngredientRead,
    summary="성분 수정 (INCI 수동 확정·플래그 해제)",
)
async def update_ingredient(
    ingredient_id: uuid.UUID,
    payload: IngredientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ingredient = await product_service.get_ingredient_owned(
        db, ingredient_id, current_user.org_id
    )
    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found"
        )
    return await product_service.update_ingredient(
        db, ingredient, payload.model_dump(exclude_unset=True)
    )


# ── Listing SPL ──────────────────────────────────────────────
@router.post(
    "/products/{product_id}/generate-spl",
    response_model=GenerateSplResponse,
    summary="제품 리스팅 SPL 생성 (Form 5067)",
)
async def generate_product_spl(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await _require_product(db, product_id, current_user)
    submission, errors = await product_service.generate_listing_submission(db, product)
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Validation failed", "errors": errors},
        )
    await audit_service.record(
        db,
        actor_id=current_user.id,
        workspace_id=product.workspace_id,
        action="product.generate_spl",
        target=f"submission:{submission.id}",
        payload={"product_id": str(product.id), "type": "5067"},
    )
    return GenerateSplResponse(
        submission=SubmissionRead.model_validate(submission),
        facility=None,  # not applicable for product listing
    )


# ── Bulk upload (FR-06) ──────────────────────────────────────
@router.post(
    "/workspaces/{workspace_id}/products/bulk",
    response_model=BulkUploadResponse,
    summary="제품 일괄 업로드 (CSV: name,category,label_url,ingredients)",
)
async def bulk_upload(
    workspace: Workspace = Depends(get_path_workspace),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    results: list[BulkRowResult] = []
    created = 0

    for idx, row in enumerate(reader, start=1):
        errors: list[str] = []
        name = (row.get("name") or "").strip()
        if not name:
            errors.append("name 필수")
        if errors:
            results.append(BulkRowResult(row=idx, errors=errors))
            continue

        product = await product_service.create(
            db,
            workspace_id=workspace.id,
            data={
                "name": name,
                "category": (row.get("category") or "").strip() or None,
                "label_url": (row.get("label_url") or "").strip() or None,
            },
        )
        ing_field = (row.get("ingredients") or "").strip()
        if ing_field:
            raw_names = [r.strip() for r in ing_field.split(";") if r.strip()]
            if raw_names:
                await product_service.add_ingredients_bulk(
                    db, product_id=product.id, raw_names=raw_names
                )
        created += 1
        results.append(BulkRowResult(row=idx, product_id=product.id))

    failed = sum(1 for r in results if r.errors)
    return BulkUploadResponse(created=created, failed=failed, results=results)
