"""Compliance deadline computation (spec §7.1).

Pure date arithmetic — no DB. Rules:

    시설 등록 완료      → +2년 갱신
    신제품 출시일 입력   → +120일 리스팅 마감
    성분/라벨 변경      → +120일 업데이트 마감
    연간 업데이트        → +1년 (동일월)
    SAE 접수            → +15영업일 (주말/공휴일 제외)
"""

from collections.abc import Iterable
from datetime import date, timedelta

from app.models.enums import ComplianceTaskStatus, ComplianceTaskType

# A task within this many days of its due date is flagged "due_soon".
DUE_SOON_WINDOW_DAYS = 30

LISTING_DEADLINE_DAYS = 120
CONTENT_UPDATE_DEADLINE_DAYS = 120
SAE_REPORT_BUSINESS_DAYS = 15
FACILITY_RENEWAL_YEARS = 2


def add_years(d: date, years: int) -> date:
    """Add calendar years, clamping Feb 29 → Feb 28 in non-leap years."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def add_business_days(
    start: date, business_days: int, holidays: Iterable[date] | None = None
) -> date:
    """Add N business days, skipping weekends and any supplied holidays."""
    holiday_set = set(holidays or ())
    current = start
    remaining = business_days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() >= 5:  # Sat=5, Sun=6
            continue
        if current in holiday_set:
            continue
        remaining -= 1
    return current


def compute_due_date(
    task_type: ComplianceTaskType,
    event_date: date,
    holidays: Iterable[date] | None = None,
) -> date:
    """Map a task type + triggering event date to its statutory due date."""
    if task_type == ComplianceTaskType.facility_renewal:
        return add_years(event_date, FACILITY_RENEWAL_YEARS)
    if task_type == ComplianceTaskType.product_listing:
        return event_date + timedelta(days=LISTING_DEADLINE_DAYS)
    if task_type == ComplianceTaskType.content_update:
        return event_date + timedelta(days=CONTENT_UPDATE_DEADLINE_DAYS)
    if task_type == ComplianceTaskType.annual_update:
        return add_years(event_date, 1)
    if task_type == ComplianceTaskType.sae_report:
        return add_business_days(event_date, SAE_REPORT_BUSINESS_DAYS, holidays)
    raise ValueError(f"Unknown task type: {task_type}")


def compute_status(
    due_date: date, today: date, *, done: bool = False
) -> ComplianceTaskStatus:
    """Derive the live status from the due date (unless already done)."""
    if done:
        return ComplianceTaskStatus.done
    if due_date < today:
        return ComplianceTaskStatus.overdue
    if (due_date - today).days <= DUE_SOON_WINDOW_DAYS:
        return ComplianceTaskStatus.due_soon
    return ComplianceTaskStatus.scheduled
