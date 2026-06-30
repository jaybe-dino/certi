"""Enumerated status / type values (spec §5.2, §6, §8)."""

from enum import StrEnum


class PlanTier(StrEnum):
    free = "free"
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"


class UserRole(StrEnum):
    """RBAC roles (spec §8)."""

    owner = "owner"
    member = "member"
    oem_manager = "oem_manager"
    admin = "admin"


class FacilityStatus(StrEnum):
    draft = "draft"
    submitting = "submitting"
    registered = "registered"
    renewal_due = "renewal_due"
    expired = "expired"


class SubmissionType(StrEnum):
    facility = "5066"  # Form 5066 — facility registration
    product = "5067"  # Form 5067 — product listing


class SubmissionStatus(StrEnum):
    generated = "generated"
    submitted = "submitted"
    ack1 = "ack1"
    ack2 = "ack2"
    completed = "completed"
    failed = "failed"


class ComplianceTaskType(StrEnum):
    facility_renewal = "facility_renewal"  # +2y
    product_listing = "product_listing"  # +120d from launch
    content_update = "content_update"  # +120d from change
    annual_update = "annual_update"  # yearly
    sae_report = "sae_report"  # +15 business days


class ComplianceTaskStatus(StrEnum):
    scheduled = "scheduled"
    due_soon = "due_soon"
    overdue = "overdue"
    done = "done"


class InciConfidence(StrEnum):
    high = "high"  # auto-confirm
    medium = "medium"  # review flag
    low = "low"  # manual input required


class AdverseEventSeverity(StrEnum):
    non_serious = "non_serious"
    serious = "serious"


class AdverseEventStatus(StrEnum):
    received = "received"
    assessing = "assessing"
    reportable = "reportable"
    submitted = "submitted"
    closed = "closed"


class UsAgentType(StrEnum):
    partner = "partner"
    direct = "direct"


class DocumentType(StrEnum):
    dossier = "dossier"
    label = "label"
    spl = "spl"
    summary = "summary"
    other = "other"
