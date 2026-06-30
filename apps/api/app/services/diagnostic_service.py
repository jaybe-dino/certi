"""MoCRA obligation / exemption rules engine (spec FR-01).

This is a heuristic based on public FDA guidance for MoCRA. It is informational
only and not legal advice — see ``DISCLAIMER``.
"""

from app.schemas.diagnostics import (
    EXEMPTION_VOIDING_CATEGORIES,
    SMALL_BUSINESS_THRESHOLD_USD,
    ChecklistItem,
    DiagnosisRequest,
    DiagnosisResponse,
    ProductCategory,
    SalesType,
)

DISCLAIMER = (
    "본 진단은 공개된 FDA MoCRA 가이드 기반의 참고용 자동 판정이며 법률 자문이 "
    "아닙니다. 최종 의무 여부는 제품 구성·유통 구조에 따라 달라질 수 있으므로 "
    "규제 전문가의 검토를 권장합니다."
)

# Sales types that operate or use a cosmetic manufacturing/processing facility,
# and therefore trigger facility registration (Form 5066) when not exempt.
_FACILITY_SALES_TYPES = frozenset(
    {
        SalesType.own_brand_manufacturer,
        SalesType.contract_manufacturer,
        SalesType.foreign_to_us,
    }
)

# Sales types that act as the Responsible Person who must list products (Form 5067).
_LISTING_SALES_TYPES = frozenset(
    {
        SalesType.own_brand_manufacturer,
        SalesType.importer,
        SalesType.foreign_to_us,
    }
)


def _voiding_categories(categories: list[ProductCategory]) -> list[ProductCategory]:
    return [c for c in categories if c in EXEMPTION_VOIDING_CATEGORIES]


def diagnose(req: DiagnosisRequest) -> DiagnosisResponse:
    reasons: list[str] = []
    voiding = _voiding_categories(req.categories)

    under_threshold = req.annual_revenue_usd < SMALL_BUSINESS_THRESHOLD_USD
    small_business_exempt = under_threshold and not voiding

    if voiding:
        labels = ", ".join(c.value for c in voiding)
        reasons.append(
            f"소규모 면제 제외 카테고리 취급({labels}) — "
            "매출과 무관하게 등록·리스팅 의무가 적용됩니다."
        )
    if under_threshold:
        reasons.append(
            f"최근 3년 평균 매출이 소규모 기준(${SMALL_BUSINESS_THRESHOLD_USD:,}) 미만입니다."
        )
    else:
        reasons.append(
            f"최근 3년 평균 매출이 소규모 기준(${SMALL_BUSINESS_THRESHOLD_USD:,}) 이상입니다."
        )

    mandatory = not small_business_exempt

    if small_business_exempt:
        exemption_status = "small_business_exempt"
        summary = (
            "소규모 사업자 면제 대상으로 보입니다. 시설 등록·제품 리스팅·cGMP 의무는 "
            "면제되나, 안전성 입증과 유해사례 기록 의무는 유지됩니다."
        )
    else:
        exemption_status = "subject_to_mocra"
        summary = "MoCRA 의무 대상으로 보입니다. 아래 체크리스트를 확인하세요."

    checklist = _build_checklist(req, mandatory)

    return DiagnosisResponse(
        mandatory=mandatory,
        exemption_status=exemption_status,
        summary=summary,
        reasons=reasons,
        checklist=checklist,
        disclaimer=DISCLAIMER,
    )


def _build_checklist(req: DiagnosisRequest, mandatory: bool) -> list[ChecklistItem]:
    needs_facility = mandatory and req.sales_type in _FACILITY_SALES_TYPES
    needs_listing = mandatory and req.sales_type in _LISTING_SALES_TYPES
    is_foreign = req.sales_type == SalesType.foreign_to_us

    items = [
        ChecklistItem(
            key="facility_registration",
            title="시설 등록 (Facility Registration)",
            required=needs_facility,
            form="5066",
            note="제조·가공 시설 운영 시 2년마다 갱신" if needs_facility else "면제 대상으로 보임",
        ),
        ChecklistItem(
            key="product_listing",
            title="제품 리스팅 (Product Listing)",
            required=needs_listing,
            form="5067",
            note="책임자(RP)가 출시 후 120일 내 리스팅" if needs_listing else "면제 대상으로 보임",
        ),
        ChecklistItem(
            key="responsible_person",
            title="책임자(Responsible Person) 지정",
            required=mandatory,
            note="라벨 표기 기업이 RP 역할 수행",
        ),
        ChecklistItem(
            key="us_agent",
            title="US Agent 지정",
            required=is_foreign,
            note=(
                "미국 외 소재 시설은 US Agent 지정 필요"
                if is_foreign
                else "국내(미국) 소재 시 불필요"
            ),
        ),
        # These persist even for exempt small businesses.
        ChecklistItem(
            key="safety_substantiation",
            title="안전성 입증 (Safety Substantiation)",
            required=True,
            note="면제 여부와 무관하게 유지되는 의무",
        ),
        ChecklistItem(
            key="adverse_event_records",
            title="유해사례 기록·보고 체계",
            required=True,
            note="심각한 유해사례는 15영업일 내 보고",
        ),
        ChecklistItem(
            key="cgmp",
            title="cGMP (우수 제조·품질관리)",
            required=mandatory,
            note="의무 대상 시 적용",
        ),
    ]
    return items
