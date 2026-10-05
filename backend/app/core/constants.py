"""Controlled vocabularies and the complaint state model (Software Design §5.1)."""


class Role:
    USER = "USER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"
    ALL = (USER, STAFF, ADMIN)


class AccountStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ALL = (ACTIVE, INACTIVE)


class Priority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    ALL = (LOW, MEDIUM, HIGH, CRITICAL)


class Status:
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ALL = (SUBMITTED, ASSIGNED, IN_PROGRESS, ESCALATED, RESOLVED, CLOSED)
    OPEN = (SUBMITTED, ASSIGNED, IN_PROGRESS, ESCALATED)
    FINAL = (RESOLVED, CLOSED)


# Allowed transitions. Keys are the current status, values the permitted next statuses.
# SUBMITTED -> ASSIGNED happens only through the assign operation and RESOLVED only through
# the resolve operation, so both are guarded separately in the service layer.
# Escalation is performed by the SLA service for any open, unresolved complaint whose
# deadline has passed (design refinement: an overdue complaint may still be SUBMITTED or ASSIGNED).
TRANSITIONS: dict[str, set[str]] = {
    Status.SUBMITTED: {Status.ASSIGNED, Status.ESCALATED},
    Status.ASSIGNED: {Status.IN_PROGRESS, Status.ESCALATED},
    Status.IN_PROGRESS: {Status.IN_PROGRESS, Status.ESCALATED, Status.RESOLVED},
    Status.ESCALATED: {Status.IN_PROGRESS, Status.ASSIGNED},
    Status.RESOLVED: {Status.CLOSED},
    Status.CLOSED: set(),
}


def can_transition(current: str, new: str) -> bool:
    return new in TRANSITIONS.get(current, set())


class Channel:
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"


class Event:
    COMPLAINT_SUBMITTED = "COMPLAINT_SUBMITTED"
    COMPLAINT_ASSIGNED = "COMPLAINT_ASSIGNED"
    STATUS_CHANGED = "STATUS_CHANGED"
    SLA_APPROACHING = "SLA_APPROACHING"
    COMPLAINT_ESCALATED = "COMPLAINT_ESCALATED"
    COMPLAINT_RESOLVED = "COMPLAINT_RESOLVED"
    COMPLAINT_CLOSED = "COMPLAINT_CLOSED"

    ALL = (
        COMPLAINT_SUBMITTED,
        COMPLAINT_ASSIGNED,
        STATUS_CHANGED,
        SLA_APPROACHING,
        COMPLAINT_ESCALATED,
        COMPLAINT_RESOLVED,
        COMPLAINT_CLOSED,
    )


# Default SLA targets in minutes, used to seed sla_rules.
DEFAULT_SLA_MINUTES = {
    Priority.CRITICAL: 4 * 60,
    Priority.HIGH: 24 * 60,
    Priority.MEDIUM: 3 * 24 * 60,
    Priority.LOW: 7 * 24 * 60,
}
DEFAULT_APPROACHING_PERCENT = 80
