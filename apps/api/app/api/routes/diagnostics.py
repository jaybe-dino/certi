"""Free MoCRA diagnostic endpoint (spec FR-01) — public, no auth."""

from fastapi import APIRouter

from app.schemas.diagnostics import DiagnosisRequest, DiagnosisResponse
from app.services import diagnostic_service

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.post(
    "",
    response_model=DiagnosisResponse,
    summary="무료 진단 — MoCRA 의무/면제 자동 판정",
)
async def diagnose(payload: DiagnosisRequest) -> DiagnosisResponse:
    return diagnostic_service.diagnose(payload)
