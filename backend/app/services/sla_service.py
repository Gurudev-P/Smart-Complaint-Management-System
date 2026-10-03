"""SLA Monitoring and Escalation Service (FR-16–FR-19, BR-06, BR-07)."""
import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.core.constants import DEFAULT_APPROACHING_PERCENT, DEFAULT_SLA_MINUTES, Event, Status
from backend.app.core.errors import NotFound
from backend.app.core.timeutil import as_utc, utcnow
from backend.app.models import SLA, Complaint, SLARule, StatusHistory
from backend.app.repositories.complaint_repository import ComplaintRepository
from backend.app.repositories.notification_repository import NotificationRepository
from backend.app.repositories.sla_rule_repository import SLARuleRepository
from backend.app.services.notification_service import NotificationService

log = logging.getLogger(__name__)


class SLAState:
    ON_TRACK = "ON_TRACK"
    APPROACHING = "APPROACHING"
    OVERDUE = "OVERDUE"
    MET = "MET"
    BREACHED = "BREACHED"


def compute_deadline(created_at: datetime, target_minutes: int) -> datetime:
    return as_utc(created_at) + timedelta(minutes=target_minutes)


def sla_state(
    *,
    status: str,
    created_at: datetime,
    deadline: datetime,
    approaching_percent: int,
    now: datetime,
    resolved_at: datetime | None = None,
) -> str:
    created_at, deadline, now = as_utc(created_at), as_utc(deadline), as_utc(now)
    if status in Status.FINAL:
        finished = as_utc(resolved_at) or now
        return SLAState.MET if finished <= deadline else SLAState.BREACHED
    if now > deadline:
        return SLAState.OVERDUE
    total = (deadline - created_at).total_seconds()
    elapsed = (now - created_at).total_seconds()
    if total > 0 and elapsed / total * 100 >= approaching_percent:
        return SLAState.APPROACHING
    return SLAState.ON_TRACK


class SLAService:
    def __init__(self, db: Session):
        self.db = db
        self.rules = SLARuleRepository(db)
        self.complaints = ComplaintRepository(db)
        self.notifications = NotificationService(db)
        self.notification_repo = NotificationRepository(db)

    # --- configuration ---
    def rule_for(self, priority: str) -> tuple[int, int]:
        rule = self.rules.for_priority(priority)
        if rule is None:
            return DEFAULT_SLA_MINUTES[priority], DEFAULT_APPROACHING_PERCENT
        return rule.target_minutes, rule.approaching_percent

    def approaching_map(self) -> dict[str, int]:
        return {r.priority: r.approaching_percent for r in self.rules.list()}

    def update_rule(self, rule_id: uuid.UUID, target_minutes: int | None, approaching_percent: int | None) -> SLARule:
        rule = self.rules.get(rule_id)
        if rule is None:
            raise NotFound("SLA rule not found")
        if target_minutes is not None:
            rule.target_minutes = target_minutes
        if approaching_percent is not None:
            rule.approaching_percent = approaching_percent
        self.db.commit()
        return rule

    def attach_sla(self, complaint: Complaint) -> SLA:
        minutes, _ = self.rule_for(complaint.priority)
        sla = SLA(
            complaint_id=complaint.complaint_id,
            target_duration=minutes,
            deadline=compute_deadline(complaint.created_at, minutes),
            escalation_level=0,
        )
        self.db.add(sla)
        complaint.sla = sla
        return sla

    def recalculate(self, complaint: Complaint) -> None:
        minutes, _ = self.rule_for(complaint.priority)
        if complaint.sla is None:
            self.attach_sla(complaint)
            return
        complaint.sla.target_duration = minutes
        complaint.sla.deadline = compute_deadline(complaint.created_at, minutes)

    # --- monitoring (Background Scheduler -> run_sla_check) ---
    def run_check(self, system_user_id: uuid.UUID, now: datetime | None = None) -> dict:
        now = as_utc(now or utcnow())
        approaching = self.approaching_map()
        result = {"checked": 0, "approaching_notified": 0, "escalated": 0}
        for complaint in self.complaints.open_with_sla(Status.OPEN):
            result["checked"] += 1
            sla = complaint.sla
            state = sla_state(
                status=complaint.status,
                created_at=complaint.created_at,
                deadline=sla.deadline,
                approaching_percent=approaching.get(complaint.priority, DEFAULT_APPROACHING_PERCENT),
                now=now,
            )
            ref = reference(complaint.complaint_id)
            assignee = current_assignee_id(complaint)
            if state == SLAState.OVERDUE and sla.escalation_level == 0:
                # Idempotency (SDD §10.3): escalation_level is checked and set in the same transaction.
                self._escalate(complaint, system_user_id, now, f"{ref} exceeded its SLA deadline and was escalated.")
                result["escalated"] += 1
            elif state == SLAState.APPROACHING and not self.notification_repo.exists(
                complaint.complaint_id, Event.SLA_APPROACHING
            ):
                message = f"{ref} ({complaint.priority}) is approaching its SLA deadline."
                if assignee:
                    self.notifications.notify(assignee, Event.SLA_APPROACHING, message, complaint.complaint_id)
                else:
                    self.notifications.notify_admins(Event.SLA_APPROACHING, message, complaint.complaint_id)
                result["approaching_notified"] += 1
        self.db.commit()
        if result["escalated"] or result["approaching_notified"]:
            log.info("SLA check: %s", result)
        return result

    def _escalate(self, complaint: Complaint, actor_id: uuid.UUID, now: datetime, message: str) -> None:
        sla = complaint.sla
        sla.escalation_level = (sla.escalation_level or 0) + 1
        sla.escalated_at = now
        if complaint.status != Status.ESCALATED:
            self.db.add(
                StatusHistory(
                    complaint_id=complaint.complaint_id,
                    old_status=complaint.status,
                    new_status=Status.ESCALATED,
                    changed_by=actor_id,
                    changed_at=now,
                )
            )
            complaint.status = Status.ESCALATED
            complaint.updated_at = now
        assignee = current_assignee_id(complaint)
        if assignee:
            self.notifications.notify(assignee, Event.COMPLAINT_ESCALATED, message, complaint.complaint_id)
        self.notifications.notify_admins(Event.COMPLAINT_ESCALATED, message, complaint.complaint_id)
        self.notifications.notify(
            complaint.user_id, Event.STATUS_CHANGED, f"{reference(complaint.complaint_id)} has been escalated for priority handling.",
            complaint.complaint_id,
        )

    def escalate_manually(self, complaint: Complaint, actor_id: uuid.UUID) -> None:
        self._escalate(complaint, actor_id, utcnow(), f"{reference(complaint.complaint_id)} was escalated by an administrator.")


def reference(complaint_id: uuid.UUID) -> str:
    return "CMP-" + complaint_id.hex[:8].upper()


def current_assignee_id(complaint: Complaint) -> uuid.UUID | None:
    for assignment in complaint.assignments:
        if assignment.ended_at is None:
            return assignment.staff_id
    return None
