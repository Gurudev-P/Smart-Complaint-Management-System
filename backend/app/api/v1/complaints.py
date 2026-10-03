import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.errors import ValidationFailed
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.schemas.complaint import (
    AssignmentRequest,
    ComplaintCreateRequest,
    ComplaintDetail,
    ComplaintPage,
    ComplaintUpdateRequest,
    ResolutionRequest,
    StatusUpdateRequest,
)
from backend.app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/complaints", tags=["Complaints"])

STATUS_RE = "^(SUBMITTED|ASSIGNED|IN_PROGRESS|ESCALATED|RESOLVED|CLOSED)$"


@router.post("", response_model=ComplaintDetail, status_code=status.HTTP_201_CREATED)
def submit_complaint(body: ComplaintCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = ComplaintService(db)
    complaint = service.create(user, body.category_id, body.priority, body.description)
    return service.detail(user, complaint)


@router.get("", response_model=ComplaintPage)
def list_complaints(
    scope: str | None = Query(default=None, pattern="^(mine|assigned|unassigned|all)$"),
    status_: list[str] | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    category_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=100),
    overdue: bool = False,
    created_from: datetime | None = Query(default=None, alias="from"),
    created_to: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for s in status_ or []:
        if not re.match(STATUS_RE, s):
            raise ValidationFailed(f"Invalid status filter: {s}")
    service = ComplaintService(db)
    items, total = service.list_for(
        user, scope=scope, status=status_, priority=priority, category_id=category_id, search=q,
        overdue=overdue, created_from=created_from, created_to=created_to, limit=limit, offset=offset,
    )
    approaching = service.sla.approaching_map()
    return {
        "items": [service.summary(c, approaching) for c in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{complaint_id}", response_model=ComplaintDetail)
def get_complaint(complaint_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = ComplaintService(db)
    return service.detail(user, service.get_for(user, complaint_id))


@router.patch("/{complaint_id}", response_model=ComplaintDetail)
def update_complaint(
    complaint_id: uuid.UUID, body: ComplaintUpdateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service = ComplaintService(db)
    return service.detail(user, service.update(user, complaint_id, body.model_dump()))


@router.patch("/{complaint_id}/status", response_model=ComplaintDetail)
def change_status(
    complaint_id: uuid.UUID, body: StatusUpdateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service = ComplaintService(db)
    return service.detail(user, service.change_status(user, complaint_id, body.new_status, body.expected_status))


@router.post("/{complaint_id}/assign", response_model=ComplaintDetail)
def assign_complaint(
    complaint_id: uuid.UUID, body: AssignmentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service = ComplaintService(db)
    return service.detail(user, service.assign(user, complaint_id, body.staff_id))


@router.post("/{complaint_id}/resolve", response_model=ComplaintDetail)
def resolve_complaint(
    complaint_id: uuid.UUID, body: ResolutionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service = ComplaintService(db)
    return service.detail(user, service.resolve(user, complaint_id, body.resolution_details))
