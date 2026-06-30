"""Pure deadline-engine unit tests (spec §7.1). No DB/app required."""

from datetime import date

from app.models.enums import ComplianceTaskStatus, ComplianceTaskType
from app.services import deadline_engine as de


def test_facility_renewal_plus_two_years():
    due = de.compute_due_date(ComplianceTaskType.facility_renewal, date(2026, 6, 30))
    assert due == date(2028, 6, 30)


def test_leap_day_renewal_clamps():
    due = de.compute_due_date(ComplianceTaskType.annual_update, date(2024, 2, 29))
    assert due == date(2025, 2, 28)


def test_product_listing_plus_120_days():
    due = de.compute_due_date(ComplianceTaskType.product_listing, date(2026, 1, 1))
    assert due == date(2026, 5, 1)  # 31+28+31+30 = 120


def test_sae_15_business_days_skips_weekends():
    # 2026-06-30 is a Tuesday; +15 business days lands on 2026-07-21 (Tue).
    due = de.compute_due_date(ComplianceTaskType.sae_report, date(2026, 6, 30))
    assert due == date(2026, 7, 21)
    assert due.weekday() < 5


def test_sae_skips_supplied_holidays():
    base = date(2026, 6, 30)
    no_holiday = de.compute_due_date(ComplianceTaskType.sae_report, base)
    with_holiday = de.add_business_days(base, 15, holidays={date(2026, 7, 3)})
    assert with_holiday == no_holiday + __import__("datetime").timedelta(days=1)


def test_status_transitions():
    today = date(2026, 6, 30)
    assert (
        de.compute_status(date(2026, 6, 29), today) == ComplianceTaskStatus.overdue
    )
    assert (
        de.compute_status(date(2026, 7, 10), today) == ComplianceTaskStatus.due_soon
    )
    assert (
        de.compute_status(date(2026, 12, 1), today) == ComplianceTaskStatus.scheduled
    )
    assert (
        de.compute_status(date(2026, 1, 1), today, done=True)
        == ComplianceTaskStatus.done
    )
