"""INCI mapping engine (spec FR-07, §7.2).

Maps a raw (Korean/common) ingredient name to a standard INCI name with a
confidence level:

    정확 일치  → high   → 자동 확정 (flag=False)
    유사/후보  → medium → 검수 플래그 (flag=True)
    미발견     → low    → 수동 입력 요청 (flag=True, inci_name=None)
"""

import re
from dataclasses import dataclass
from difflib import get_close_matches

from app.models.enums import InciConfidence
from app.services.inci_data import INCI_DICTIONARY

# Precompute normalized keys once.
_NORMALIZED: dict[str, str] = {}


def _normalize(name: str) -> str:
    """Lowercase, drop spaces and common separators for robust matching."""
    return re.sub(r"[\s\-_/().]", "", name.strip().lower())


def _ensure_index() -> None:
    if not _NORMALIZED:
        for key, inci in INCI_DICTIONARY.items():
            _NORMALIZED[_normalize(key)] = inci


@dataclass
class InciMatch:
    inci_name: str | None
    confidence: InciConfidence
    flag: bool


def map_ingredient(raw_name: str) -> InciMatch:
    _ensure_index()
    norm = _normalize(raw_name)
    if not norm:
        return InciMatch(None, InciConfidence.low, True)

    # 1) Exact normalized match → high confidence, auto-confirm.
    if norm in _NORMALIZED:
        return InciMatch(_NORMALIZED[norm], InciConfidence.high, False)

    # 2) Substring containment either direction → medium, needs review.
    for key, inci in _NORMALIZED.items():
        if key in norm or norm in key:
            return InciMatch(inci, InciConfidence.medium, True)

    # 3) Fuzzy match against known keys → medium, needs review.
    close = get_close_matches(norm, list(_NORMALIZED.keys()), n=1, cutoff=0.8)
    if close:
        return InciMatch(_NORMALIZED[close[0]], InciConfidence.medium, True)

    # 4) No match → low, manual input required.
    return InciMatch(None, InciConfidence.low, True)
