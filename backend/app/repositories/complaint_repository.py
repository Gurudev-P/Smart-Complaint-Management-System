import uuid
from datetime import datetime

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import SLA, Assignment, Category, Complaint, StatusHistory


class ComplaintRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, complaint_id: uuid.UUID) -> Complaint | None:
        stmt = (
            select(Complaint)
            .where(Complaint.complaint_id == complaint_id)
            .options(
                selectinload(Complaint.category),
                selectinload(Complaint.creator),
                selectinload(Complaint.assignments).selectinload(Assignment.staff),
                selectinload(Complaint.status_history).selectinload(StatusHistory.changer),
                selectinload(Complaint.sla),
                selectinload(Complaint.resolution),
            )
            .execution_options(populate_existing=True)
        )
        return self.db.scalar(stmt)

    def add(self, complaint: Complaint) -> Complaint:
        self.db.add(complaint)
        self.db.flush()
        return complaint

    @staticmethod
    def active_assignment_clause(staff_id: uuid.UUID):
        return Complaint.assignments.any(
            and_(Assignment.staff_id == staff_id, Assignment.ended_at.is_(None))
        )

    def build_query(
        self,
        *,
        creator_id: uuid.UUID | None = None,
        assigned_to: uuid.UUID | None = None,
        status: list[str] | None = None,
        priority: str | None = None,
        category_id: uuid.UUID | None = None,
        search: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        overdue_before: datetime | None = None,
    ) -> Select:
        stmt = select(Complaint)
        if creator_id:
            stmt = stmt.where(Complaint.user_id == creator_id)
        if assigned_to:
            stmt = stmt.where(self.active_assignment_clause(assigned_to))
        if status:
            stmt = stmt.where(Complaint.status.in_(status))
        if priority:
            stmt = stmt.where(Complaint.priority == priority)
        if category_id:
            stmt = stmt.where(Complaint.category_id == category_id)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Complaint.description.ilike(like),
                    Complaint.category.has(Category.name.ilike(like)),
                )
            )
        if created_from:
            stmt = stmt.where(Complaint.created_at >= created_from)
        if created_to:
            stmt = stmt.where(Complaint.created_at <= created_to)
        if overdue_before:
            stmt = stmt.where(Complaint.sla.has(SLA.deadline < overdue_before))
        return stmt

    def page(self, stmt: Select, limit: int, offset: int) -> tuple[list[Complaint], int]:
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.db.scalars(
            stmt.options(
                selectinload(Complaint.category),
                selectinload(Complaint.creator),
                selectinload(Complaint.assignments).selectinload(Assignment.staff),
                selectinload(Complaint.sla),
            )
            .order_by(Complaint.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows), total

    def open_with_sla(self, open_statuses: tuple[str, ...]) -> list[Complaint]:
        stmt = (
            select(Complaint)
            .join(SLA, SLA.complaint_id == Complaint.complaint_id)
            .where(Complaint.status.in_(open_statuses))
            .options(
                selectinload(Complaint.sla),
                selectinload(Complaint.assignments),
                selectinload(Complaint.category),
            )
        )
        return list(self.db.scalars(stmt))
