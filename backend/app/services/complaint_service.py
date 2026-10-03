"""Complaint, Assignment and Resolution services (FR-05–FR-15, BR-01–BR-05, BR-08, BR-10)."""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import AccountStatus, Event, Priority, Role, Status, can_transition
from backend.app.core.errors import Conflict, Forbidden, NotFound, ValidationFailed
from backend.app.core.timeutil import as_utc, utcnow
from backend.app.models import Assignment, Complaint, Resolution, StatusHistory, User
from backend.app.repositories.category_repository import CategoryRepository
from backend.app.repositories.complaint_repository import ComplaintRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.services.notification_service import NotificationService
from backend.app.services.sla_service import (
    SLAService,
    current_assignee_id,
    reference,
    sla_state,
)

STATUS_LABEL = {
    Status.SUBMITTED: "Submitted",
    Status.ASSIGNED: "Assigned",
    Status.IN_PROGRESS: "In Progress",
    Status.ESCALATED: "Escalated",
    Status.RESOLVED: "Resolved",
    Status.CLOSED: "Closed",
}


class ComplaintService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ComplaintRepository(db)
        self.categories = CategoryRepository(db)
        self.users = UserRepository(db)
        self.sla = SLAService(db)
        self.notifications = NotificationService(db)

    # ------------------------------------------------------------------ access
    def can_view(self, user: User, complaint: Complaint) -> bool:
        if user.role == Role.ADMIN or complaint.user_id == user.user_id:
            return True
        if user.role == Role.STAFF:
            if current_assignee_id(complaint) == user.user_id:
                return True
            if settings.STAFF_CAN_ASSIGN and complaint.status in Status.OPEN:
                return True
        return False

    def can_assign(self, user: User) -> bool:
        return user.role == Role.ADMIN or (user.role == Role.STAFF and settings.STAFF_CAN_ASSIGN)

    def _is_handler(self, user: User, complaint: Complaint) -> bool:
        return user.role == Role.ADMIN or (
            user.role == Role.STAFF and current_assignee_id(complaint) == user.user_id
        )

    def permissions(self, user: User, complaint: Complaint) -> dict[str, bool]:
        handler = self._is_handler(user, complaint)
        is_creator = complaint.user_id == user.user_id
        return {
            "edit": is_creator and complaint.status == Status.SUBMITTED,
            "change_priority": handler and complaint.status in Status.OPEN,
            "assign": self.can_assign(user) and complaint.status in Status.OPEN,
            "start": handler and complaint.status in (Status.ASSIGNED, Status.ESCALATED),
            "resolve": handler and complaint.status == Status.IN_PROGRESS,
            "escalate": user.role == Role.ADMIN and complaint.status in Status.OPEN,
            "close": user.role == Role.ADMIN and complaint.status == Status.RESOLVED,
        }

    def get_for(self, user: User, complaint_id: uuid.UUID) -> Complaint:
        complaint = self.repo.get(complaint_id)
        # Not-accessible complaints are reported as not found so their existence is not leaked (SDD §9.5).
        if complaint is None or not self.can_view(user, complaint):
            raise NotFound("Complaint not found")
        return complaint

    # ------------------------------------------------------------------ create / list
    def create(self, user: User, category_id: uuid.UUID, priority: str, description: str) -> Complaint:
        category = self.categories.get(category_id)
        if category is None or not category.active_flag:
            raise ValidationFailed("Select a valid, active category")
        if priority not in Priority.ALL:
            raise ValidationFailed("Invalid priority")
        now = utcnow()
        complaint = Complaint(
            user_id=user.user_id,
            category_id=category.category_id,
            priority=priority,
            description=description,
            status=Status.SUBMITTED,
            created_at=now,
            updated_at=now,
        )
        self.repo.add(complaint)
        self.sla.attach_sla(complaint)
        self.db.add(
            StatusHistory(
                complaint_id=complaint.complaint_id,
                old_status=Status.SUBMITTED,
                new_status=Status.SUBMITTED,
                changed_by=user.user_id,
                changed_at=now,
            )
        )
        ref = reference(complaint.complaint_id)
        self.notifications.notify(
            user.user_id, Event.COMPLAINT_SUBMITTED, f"{ref} was submitted successfully.", complaint.complaint_id
        )
        if priority in (Priority.HIGH, Priority.CRITICAL):
            self.notifications.notify_admins(
                Event.COMPLAINT_SUBMITTED, f"New {priority} complaint {ref} needs assignment.", complaint.complaint_id
            )
        self.db.commit()
        return self.repo.get(complaint.complaint_id)

    def list_for(
        self,
        user: User,
        *,
        scope: str | None,
        status: list[str] | None,
        priority: str | None,
        category_id: uuid.UUID | None,
        search: str | None,
        overdue: bool,
        created_from: datetime | None,
        created_to: datetime | None,
        limit: int,
        offset: int,
    ):
        filters = dict(
            status=status, priority=priority, category_id=category_id, search=search,
            created_from=created_from, created_to=created_to,
            overdue_before=utcnow() if overdue else None,
        )
        if overdue and not status:
            filters["status"] = list(Status.OPEN)
        if user.role == Role.USER:
            scope = "mine"
        elif user.role == Role.STAFF:
            scope = scope or "assigned"
            if scope == "all":
                raise Forbidden("Staff cannot list all complaints")
            if scope == "unassigned" and not settings.STAFF_CAN_ASSIGN:
                raise Forbidden("Staff are not permitted to assign complaints")
        else:
            scope = scope or "all"

        if scope == "mine":
            stmt = self.repo.build_query(creator_id=user.user_id, **filters)
        elif scope == "assigned":
            stmt = self.repo.build_query(assigned_to=user.user_id, **filters)
        elif scope == "unassigned":
            if not filters["status"]:
                filters["status"] = [Status.SUBMITTED, Status.ESCALATED]
            stmt = self.repo.build_query(**filters).where(
                ~Complaint.assignments.any(Assignment.ended_at.is_(None))
            )
        elif scope == "all":
            stmt = self.repo.build_query(**filters)
        else:
            raise ValidationFailed("Unknown scope")
        return self.repo.page(stmt, limit, offset)

    # ------------------------------------------------------------------ update
    def update(self, user: User, complaint_id: uuid.UUID, changes: dict) -> Complaint:
        complaint = self.get_for(user, complaint_id)
        perms = self.permissions(user, complaint)
        changes = {k: v for k, v in changes.items() if v is not None}
        if not changes:
            raise ValidationFailed("No changes supplied")
        if "priority" in changes and changes["priority"] != complaint.priority:
            if not perms["change_priority"]:
                raise Forbidden("Only the assigned staff member or an administrator can change priority")
            complaint.priority = changes["priority"]
            self.sla.recalculate(complaint)
        if "description" in changes or "category_id" in changes:
            if not perms["edit"]:
                raise Forbidden("Only the creator can edit a complaint, and only before it is assigned")
            if "category_id" in changes:
                category = self.categories.get(changes["category_id"])
                if category is None or not category.active_flag:
                    raise ValidationFailed("Select a valid, active category")
                complaint.category_id = category.category_id
            if "description" in changes:
                complaint.description = changes["description"]
        complaint.updated_at = utcnow()
        self.db.commit()
        return self.repo.get(complaint.complaint_id)

    def _record_status(self, complaint: Complaint, new_status: str, actor: User) -> None:
        old = complaint.status
        complaint.status = new_status
        complaint.updated_at = utcnow()
        self.db.add(
            StatusHistory(
                complaint_id=complaint.complaint_id,
                old_status=old,
                new_status=new_status,
                changed_by=actor.user_id,
                changed_at=complaint.updated_at,
            )
        )
        if complaint.user_id != actor.user_id:
            self.notifications.notify(
                complaint.user_id,
                Event.STATUS_CHANGED,
                f"{reference(complaint.complaint_id)} is now {STATUS_LABEL[new_status]}.",
                complaint.complaint_id,
            )

    def change_status(self, user: User, complaint_id: uuid.UUID, new_status: str, expected: str | None) -> Complaint:
        complaint = self.get_for(user, complaint_id)
        if expected and expected != complaint.status:
            raise Conflict(f"Complaint status changed to {complaint.status}; refresh and try again")
        if new_status == Status.ASSIGNED:
            raise ValidationFailed("Use the assign operation to assign a complaint")
        if new_status == Status.RESOLVED:
            raise ValidationFailed("Use the resolve operation; resolution details are required (BR-05)")
        if new_status == Status.SUBMITTED or not can_transition(complaint.status, new_status):
            raise ValidationFailed(f"Invalid status transition {complaint.status} → {new_status}")

        if new_status == Status.IN_PROGRESS:
            if not self._is_handler(user, complaint):
                raise Forbidden("Only the assigned staff member or an administrator can update this complaint")
            if complaint.status == Status.ESCALATED and current_assignee_id(complaint) is None:
                raise ValidationFailed("Assign the escalated complaint to a staff member first")
        elif new_status == Status.ESCALATED:
            if user.role != Role.ADMIN:
                raise Forbidden("Only administrators can escalate manually")
            self.sla.escalate_manually(complaint, user.user_id)
            self.db.commit()
            return self.repo.get(complaint.complaint_id)
        elif new_status == Status.CLOSED:
            if user.role != Role.ADMIN:
                raise Forbidden("Only administrators can close complaints")
        self._record_status(complaint, new_status, user)
        self.db.commit()
        return self.repo.get(complaint.complaint_id)

    def assign(self, user: User, complaint_id: uuid.UUID, staff_id: uuid.UUID) -> Complaint:
        if not self.can_assign(user):
            raise Forbidden("You are not permitted to assign complaints")
        complaint = self.get_for(user, complaint_id)
        if complaint.status not in Status.OPEN:
            raise ValidationFailed(f"A {complaint.status} complaint cannot be assigned")
        staff = self.users.get(staff_id)
        if staff is None or staff.role != Role.STAFF or staff.account_status != AccountStatus.ACTIVE:
            raise ValidationFailed("The selected user is not an active staff member")
        current = current_assignee_id(complaint)
        if current == staff_id:
            raise Conflict("The complaint is already assigned to this staff member")
        now = utcnow()
        for assignment in complaint.assignments:
            if assignment.ended_at is None:
                assignment.ended_at = now
        self.db.add(Assignment(complaint_id=complaint.complaint_id, staff_id=staff_id, assigned_at=now))
        if complaint.status in (Status.SUBMITTED, Status.ESCALATED):
            self._record_status(complaint, Status.ASSIGNED, user)
        else:
            complaint.updated_at = now
        self.notifications.notify(
            staff_id,
            Event.COMPLAINT_ASSIGNED,
            f"{reference(complaint.complaint_id)} ({complaint.priority}) has been assigned to you.",
            complaint.complaint_id,
        )
        self.db.commit()
        self.db.expire(complaint)
        return self.repo.get(complaint.complaint_id)

    def resolve(self, user: User, complaint_id: uuid.UUID, details: str) -> Complaint:
        complaint = self.get_for(user, complaint_id)
        if not self._is_handler(user, complaint):
            raise Forbidden("Only the assigned staff member or an administrator can resolve this complaint")
        if complaint.status != Status.IN_PROGRESS:
            raise ValidationFailed("Only an In Progress complaint can be resolved")
        if complaint.resolution is not None:
            raise Conflict("This complaint already has a resolution")
        if not details or not details.strip():
            raise ValidationFailed("Resolution details are required (BR-05)")
        now = utcnow()
        # Resolution record and RESOLVED status are written in one transaction (SDD §8.2).
        self.db.add(
            Resolution(
                complaint_id=complaint.complaint_id,
                resolver_id=user.user_id,
                resolution_details=details.strip(),
                resolved_at=now,
            )
        )
        self._record_status(complaint, Status.RESOLVED, user)
        self.db.commit()
        self.db.expire(complaint)
        return self.repo.get(complaint.complaint_id)

    # ------------------------------------------------------------------ serialisation
    def summary(self, complaint: Complaint, approaching: dict[str, int] | None = None) -> dict:
        approaching = approaching if approaching is not None else self.sla.approaching_map()
        assignee = None
        for assignment in complaint.assignments:
            if assignment.ended_at is None:
                assignee = assignment.staff
        sla = complaint.sla
        resolved_at = complaint.resolution.resolved_at if complaint.resolution else None
        return {
            "complaint_id": complaint.complaint_id,
            "reference": reference(complaint.complaint_id),
            "description": complaint.description,
            "priority": complaint.priority,
            "status": complaint.status,
            "category": complaint.category,
            "creator": complaint.creator,
            "assignee": assignee,
            "created_at": as_utc(complaint.created_at),
            "updated_at": as_utc(complaint.updated_at),
            "sla": None
            if sla is None
            else {
                "target_duration": sla.target_duration,
                "deadline": as_utc(sla.deadline),
                "escalation_level": sla.escalation_level,
                "escalated_at": as_utc(sla.escalated_at),
                "state": sla_state(
                    status=complaint.status,
                    created_at=complaint.created_at,
                    deadline=sla.deadline,
                    approaching_percent=approaching.get(complaint.priority, 80),
                    now=utcnow(),
                    resolved_at=resolved_at,
                ),
            },
        }

    def detail(self, user: User, complaint: Complaint) -> dict:
        data = self.summary(complaint)
        data["history"] = [
            {
                "old_status": h.old_status,
                "new_status": h.new_status,
                "changed_at": as_utc(h.changed_at),
                "changed_by": h.changer,
            }
            for h in sorted(complaint.status_history, key=lambda h: as_utc(h.changed_at))
        ]
        data["resolution"] = (
            None
            if complaint.resolution is None
            else {
                "resolution_details": complaint.resolution.resolution_details,
                "resolved_at": as_utc(complaint.resolution.resolved_at),
                "resolver": complaint.resolution.resolver,
            }
        )
        data["permissions"] = self.permissions(user, complaint)
        return data
