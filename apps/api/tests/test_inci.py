"""INCI mapping engine unit tests (spec FR-07, §7.2). No DB required."""

from app.models.enums import InciConfidence
from app.services.inci_service import map_ingredient


def test_exact_match_high_confidence():
    m = map_ingredient("정제수")
    assert m.inci_name == "Water"
    assert m.confidence == InciConfidence.high
    assert m.flag is False


def test_normalization_ignores_spaces_and_case():
    m = map_ingredient("  나이아신아마이드 ")
    assert m.inci_name == "Niacinamide"
    assert m.confidence == InciConfidence.high


def test_substring_match_medium_flagged():
    m = map_ingredient("정제수(물)100%")
    # Normalizes to include '정제수' → containment → medium, flagged.
    assert m.inci_name == "Water"
    assert m.confidence == InciConfidence.medium
    assert m.flag is True


def test_unknown_low_confidence_manual():
    m = map_ingredient("완전알수없는성분xyz")
    assert m.inci_name is None
    assert m.confidence == InciConfidence.low
    assert m.flag is True


def test_empty_is_low():
    m = map_ingredient("   ")
    assert m.confidence == InciConfidence.low
