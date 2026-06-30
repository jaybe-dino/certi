"""Submission validators (spec §7.3 검증기 체크).

Checks: 필수값 · 영문 입력 · FEI 형식. Schema validation of the generated SPL
is handled separately by the SPL service.
"""

import re

from app.models.facility import Facility

# FDA Facility Establishment Identifier: numeric, typically 7–10 digits.
_FEI_PATTERN = re.compile(r"^\d{7,10}$")


def _is_ascii(value: str) -> bool:
    return value.isascii()


def validate_facility_for_submission(facility: Facility) -> list[str]:
    """Return a list of human-readable errors; empty means valid."""
    errors: list[str] = []

    # 필수값
    if not facility.name_en:
        errors.append("시설명(영문)은 필수입니다.")
    if not facility.address_en:
        errors.append("시설 주소(영문)는 필수입니다.")
    if not facility.email:
        errors.append("시설 연락 이메일은 필수입니다.")
    if not facility.fei:
        errors.append("FEI 번호는 필수입니다.")

    # 영문 입력
    if facility.name_en and not _is_ascii(facility.name_en):
        errors.append("시설명은 영문(ASCII)으로 입력해야 합니다.")
    if facility.address_en and not _is_ascii(facility.address_en):
        errors.append("시설 주소는 영문(ASCII)으로 입력해야 합니다.")

    # FEI 형식
    if facility.fei and not _FEI_PATTERN.match(facility.fei):
        errors.append("FEI 번호 형식이 올바르지 않습니다 (숫자 7~10자리).")

    return errors
