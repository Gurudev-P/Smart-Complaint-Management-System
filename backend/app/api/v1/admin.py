"""Categories, SLA rules, notifications and reports (Software Design §9.3)."""
import csv
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.constants import Event, Role
from backend.app.core.errors import Conflict, NotFound, ValidationFailed
from backend.app.core.timeutil import as_utc
from backend.app.db.session import get_db
from backend.app.models import Category, User
from backend.app.repositories.category_repository import CategoryRepository
from backend.app.repositories.sla_rule_repository import SLARuleRepository
from backend.app.schemas.admin import (
    CategoryCreateRequest,
    CategoryOut,
    CategoryUpdateRequest,
    NotificationOut,
    NotificationPage,
    SLACheckResult,
    SLARuleOut,
    SLARuleUpdateRequest,
)
from backend.app.schemas.complaint import ComplaintPage
from backend.app.services.auth_service import AuthService
from backend.app.services.complaint_service import ComplaintService
from backend.app.services.notification_service import NotificationService
from backend.app.services.report_service import ReportService
from backend.app.services.sla_service import SLAService

categories = APIRouter(prefix="/categories", tags=["Categories"])
sla = APIRouter(prefix="/sla", tags=["SLA"])
notifications = APIRouter(prefix="/notifications", tags=["Notifications"])
reports = APIRouter(prefix="/reports", tags=["Reports"])


# ---------------------------------------------------------------- categories (FR-09)
@categories.get("", response_model=list[CategoryOut])
def list_categories(
    include_inactive: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return CategoryRepository(db).list(include_inactive=include_inactive and user.role == Role.ADMIN)


@categories.post("", response_model=CategoryOut, status_code=201)
def create_category(body: CategoryCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN))):
    repo = CategoryRepository(db)
    if repo.get_by_name(body.name):
        raise Conflict("A category with this name already exists")
    category = repo.add(Category(name=body.name, description=body.description, active_flag=True))
    db.commit()
    return category


@categories.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: uuid.UUID, body: CategoryUpdateRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN))
):
    repo = CategoryRepository(db)
    category = repo.get(category_id)
    if category is None:
        raise NotFound("Category not found")
    if body.name and body.name.strip().lower() != category.name.lower():
        if repo.get_by_name(body.name.strip()):
            raise Conflict("A category with this name already exists")
        category.name = body.name.strip()
    if body.description is not None:
        category.description = body.description
    if body.active_flag is not None:
        category.active_flag = body.active_flag
    db.commit()
    return category


# ---------------------------------------------------------------- SLA (FR-16–FR-19)
@sla.get("/rules", response_model=list[SLARuleOut])
def list_rules(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN))):
    return SLARuleRepository(db).list()


@sla.patch("/rules/{rule_id}", response_model=SLARuleOut)
def update_rule(
    rule_id: uuid.UUID, body: SLARuleUpdateRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN))
):
    return SLAService(db).update_rule(rule_id, body.target_minutes, body.approaching_percent)


@sla.post("/check", response_model=SLACheckResult)
def run_check(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN))):
    """Runs the same SLA scan as the background scheduler, on demand."""
    system = AuthService(db).ensure_system_user()
    return SLAService(db).run_check(system.user_id)


# ---------------------------------------------------------------- notifications (FR-20, FR-21)
@notifications.get("", response_model=NotificationPage)
def list_notifications(
    unread_only: bool = False,
    event_type: str | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if event_type is not None and event_type not in Event.ALL:
        raise ValidationFailed("Unsupported notification event type")

    items, unread = NotificationService(db).list_for(
        user,
        unread_only=unread_only,
        limit=limit,
        event_type=event_type,
    )
    return {"items": items, "unread": unread}


@notifications.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return NotificationService(db).mark_read(user, notification_id)


@notifications.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"updated": NotificationService(db).mark_all_read(user)}


# ---------------------------------------------------------------- reports (FR-22–FR-24)
@reports.get("/summary")
def report_summary(
    created_from: datetime | None = Query(default=None, alias="from"),
    created_to: datetime | None = Query(default=None, alias="to"),
    category_id: uuid.UUID | None = None,
    priority: str | None = Query(default=None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.STAFF)),
):
    return ReportService(db).summary(
        user, created_from=created_from, created_to=created_to, category_id=category_id, priority=priority
    )


@reports.get("/complaints", response_model=ComplaintPage)
def report_complaints(
    status_: list[str] | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    category_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=100),
    overdue: bool = False,
    created_from: datetime | None = Query(default=None, alias="from"),
    created_to: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN)),
):
    service = ComplaintService(db)
    items, total = service.list_for(
        admin, scope="all", status=status_, priority=priority, category_id=category_id, search=q,
        overdue=overdue, created_from=created_from, created_to=created_to, limit=limit, offset=offset,
    )
    approaching = service.sla.approaching_map()
    return {"items": [service.summary(c, approaching) for c in items], "total": total, "limit": limit, "offset": offset}


@reports.get("/complaints.csv")
def report_complaints_csv(
    status_: list[str] | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    category_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=100),
    overdue: bool = False,
    created_from: datetime | None = Query(default=None, alias="from"),
    created_to: datetime | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN)),
):
    service = ComplaintService(db)
    items, _ = service.list_for(
    admin,
    scope="all",
    status=status_,
    priority=priority,
    category_id=category_id,
    search=q,
    overdue=overdue,
    created_from=created_from,
    created_to=created_to,
    limit=10_000,
    offset=0,
)
    approaching = service.sla.approaching_map()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Reference", "Created (UTC)", "Category", "Priority", "Status", "Creator", "Assignee", "SLA deadline (UTC)", "SLA state"])
    for c in items:
        s = service.summary(c, approaching)
        writer.writerow([
            s["reference"], as_utc(c.created_at).strftime("%Y-%m-%d %H:%M"), s["category"].name, s["priority"], s["status"],
            s["creator"].name, s["assignee"].name if s["assignee"] else "",
            s["sla"]["deadline"].strftime("%Y-%m-%d %H:%M") if s["sla"] else "", s["sla"]["state"] if s["sla"] else "",
        ])
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="complaints_report.csv"'},
    )
