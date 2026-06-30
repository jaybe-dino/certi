"""Product persistence: listing, ingredients (INCI), linking, SPL (FR-05/06/07)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InciConfidence, SubmissionStatus, SubmissionType
from app.models.facility import Facility, ProductFacility
from app.models.organization import Workspace
from app.models.product import Ingredient, Product
from app.models.submission import Submission
from app.services import inci_service, spl_service


# ── Product CRUD ─────────────────────────────────────────────
async def create(db: AsyncSession, *, workspace_id: uuid.UUID, data: dict) -> Product:
    product = Product(workspace_id=workspace_id, **data)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def list_for_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> list[Product]:
    result = await db.execute(
        select(Product)
        .where(Product.workspace_id == workspace_id)
        .order_by(Product.created_at)
    )
    return list(result.scalars().all())


async def get_owned(
    db: AsyncSession, product_id: uuid.UUID, org_id: uuid.UUID
) -> Product | None:
    result = await db.execute(
        select(Product)
        .join(Workspace, Product.workspace_id == Workspace.id)
        .where(Product.id == product_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


async def update(db: AsyncSession, product: Product, data: dict) -> Product:
    for key, value in data.items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


# ── Ingredients / INCI (FR-07) ───────────────────────────────
async def add_ingredient(
    db: AsyncSession, *, product_id: uuid.UUID, raw_name: str, inci_name: str | None = None
) -> Ingredient:
    if inci_name:
        # Manual override is trusted: high confidence, no review flag.
        ingredient = Ingredient(
            product_id=product_id,
            raw_name=raw_name,
            inci_name=inci_name,
            confidence=InciConfidence.high,
            flag=False,
        )
    else:
        match = inci_service.map_ingredient(raw_name)
        ingredient = Ingredient(
            product_id=product_id,
            raw_name=raw_name,
            inci_name=match.inci_name,
            confidence=match.confidence,
            flag=match.flag,
        )
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


async def add_ingredients_bulk(
    db: AsyncSession, *, product_id: uuid.UUID, raw_names: list[str]
) -> list[Ingredient]:
    created: list[Ingredient] = []
    for raw in raw_names:
        match = inci_service.map_ingredient(raw)
        ing = Ingredient(
            product_id=product_id,
            raw_name=raw,
            inci_name=match.inci_name,
            confidence=match.confidence,
            flag=match.flag,
        )
        db.add(ing)
        created.append(ing)
    await db.commit()
    for ing in created:
        await db.refresh(ing)
    return created


async def list_ingredients(db: AsyncSession, product_id: uuid.UUID) -> list[Ingredient]:
    result = await db.execute(
        select(Ingredient)
        .where(Ingredient.product_id == product_id)
        .order_by(Ingredient.created_at)
    )
    return list(result.scalars().all())


async def get_ingredient_owned(
    db: AsyncSession, ingredient_id: uuid.UUID, org_id: uuid.UUID
) -> Ingredient | None:
    result = await db.execute(
        select(Ingredient)
        .join(Product, Ingredient.product_id == Product.id)
        .join(Workspace, Product.workspace_id == Workspace.id)
        .where(Ingredient.id == ingredient_id, Workspace.org_id == org_id)
    )
    return result.scalar_one_or_none()


async def update_ingredient(db: AsyncSession, ingredient: Ingredient, data: dict) -> Ingredient:
    for key, value in data.items():
        setattr(ingredient, key, value)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


# ── Facility linking ─────────────────────────────────────────
async def link_facility(
    db: AsyncSession, *, product: Product, facility_id: uuid.UUID
) -> bool:
    """Link a facility in the same workspace. Returns False if facility invalid."""
    facility = await db.get(Facility, facility_id)
    if facility is None or facility.workspace_id != product.workspace_id:
        return False
    exists = await db.get(ProductFacility, (product.id, facility_id))
    if exists is None:
        db.add(ProductFacility(product_id=product.id, facility_id=facility_id))
        await db.commit()
    return True


async def facility_feis(db: AsyncSession, product_id: uuid.UUID) -> list[str]:
    result = await db.execute(
        select(Facility.fei)
        .join(ProductFacility, ProductFacility.facility_id == Facility.id)
        .where(ProductFacility.product_id == product_id, Facility.fei.is_not(None))
    )
    return [fei for (fei,) in result.all() if fei]


# ── Listing SPL (Form 5067) ──────────────────────────────────
async def generate_listing_submission(
    db: AsyncSession, product: Product
) -> tuple[Submission | None, list[str]]:
    errors: list[str] = []
    ingredients = await list_ingredients(db, product.id)
    if not ingredients:
        errors.append("성분이 1개 이상 등록되어야 합니다.")
    flagged = [i for i in ingredients if i.flag]
    if flagged:
        errors.append(f"검수 필요 성분이 {len(flagged)}건 있습니다 (INCI 확정 후 제출).")
    feis = await facility_feis(db, product.id)
    if not feis:
        errors.append("연동된 시설(FEI)이 필요합니다.")
    if errors:
        return None, errors

    spl_xml = spl_service.generate_product_spl(product, ingredients, feis)
    submission = Submission(
        workspace_id=product.workspace_id,
        product_id=product.id,
        type=SubmissionType.product,
        spl_xml=spl_xml,
        status=SubmissionStatus.generated,
    )
    product.status = "listed"
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    await db.refresh(product)
    return submission, []
