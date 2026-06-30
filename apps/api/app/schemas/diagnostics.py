"""Free MoCRA diagnostic — request/response schemas (spec FR-01)."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ProductCategory(StrEnum):
    """Product risk category. Some categories void the small-business exemption
    under MoCRA (§612(b)) regardless of revenue."""

    general = "general"  # 일반 스킨케어/색조 등
    eye_mucosa = "eye_mucosa"  # 눈 점막 접촉 (아이라이너 등)
    injectable = "injectable"  # 주사형
    internal_use = "internal_use"  # 체내 사용
    long_wear_24h = "long_wear_24h"  # 24시간 초과 외형 변화·비제거형


# Categories that disqualify a company from the small-business exemption.
EXEMPTION_VOIDING_CATEGORIES: frozenset[ProductCategory] = frozenset(
    {
        ProductCategory.eye_mucosa,
        ProductCategory.injectable,
        ProductCategory.internal_use,
        ProductCategory.long_wear_24h,
    }
)


class SalesType(StrEnum):
    """How the company places product on the US market (판매형태)."""

    own_brand_manufacturer = "own_brand_manufacturer"  # 자체 브랜드 제조
    contract_manufacturer = "contract_manufacturer"  # OEM 수탁 제조
    importer = "importer"  # 수입·유통 (RP)
    distributor_only = "distributor_only"  # 단순 판매
    foreign_to_us = "foreign_to_us"  # 해외 → 미국 수출


# MoCRA small-business threshold: avg. gross annual sales over the prior 3 years.
SMALL_BUSINESS_THRESHOLD_USD = 1_000_000


class DiagnosisRequest(BaseModel):
    annual_revenue_usd: float = Field(
        ge=0, description="최근 3년 평균 총 매출 (USD)"
    )
    categories: list[ProductCategory] = Field(
        min_length=1, description="취급 제품 카테고리 (복수 선택 가능)"
    )
    sales_type: SalesType


class ChecklistItem(BaseModel):
    key: str
    title: str
    required: bool
    form: str | None = None
    note: str | None = None


class DiagnosisResponse(BaseModel):
    mandatory: bool
    exemption_status: str  # "small_business_exempt" | "subject_to_mocra"
    summary: str
    reasons: list[str]
    checklist: list[ChecklistItem]
    disclaimer: str
