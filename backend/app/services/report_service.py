"""Dashboard and Reporting Service (FR-22–FR-24)."""
import uuid
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, selectinload

from backend.app.core.constants import Priority, Role, Status
from backend.app.core.errors import ValidationFailed
from backend.app.core.timeutil import as_utc, utcnow
from backend.app.models import Complaint, User
from backend.app.repositories.complaint_repository import ComplaintRepository


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ComplaintRepository(db)

    def summary(
        self,
        user: User,
        *,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        category_id: uuid.UUID | None = None,
        priority: str | None = None,
        trend_days: int = 14,
    ) -> dict:
        if created_from and created_to and created_from > created_to:
            raise ValidationFailed("'from' date must be before 'to' date")
        stmt = self.repo.build_query(
            assigned_to=user.user_id if user.role == Role.STAFF else None,
            category_id=category_id,
            priority=priority,
            created_from=created_from,
            created_to=created_to,
        ).options(
            selectinload(Complaint.category),
            selectinload(Complaint.sla),
            selectinload(Complaint.resolution),
        )
        complaints = list(self.db.scalars(stmt))
        now = utcnow()

        by_status = Counter({s: 0 for s in Status.ALL})
        by_priority = Counter({p: 0 for p in Priority.ALL})
        by_category: Counter = Counter()
        overdue = escalated = resolved = met = 0
        resolution_hours: list[float] = []
        today = now.date()
        trend = Counter({(today - timedelta(days=i)).isoformat(): 0 for i in range(trend_days)})

        for c in complaints:
            by_status[c.status] += 1
            by_priority[c.priority] += 1
            by_category[c.category.name] += 1
            created = as_utc(c.created_at)
            day = created.date().isoformat()
            if day in trend:
                trend[day] += 1
            if c.sla and c.sla.escalation_level > 0:
                escalated += 1
            if c.status in Status.OPEN and c.sla and as_utc(c.sla.deadline) < now:
                overdue += 1
            if c.resolution is not None:
                resolved += 1
                resolved_at = as_utc(c.resolution.resolved_at)
                resolution_hours.append((resolved_at - created).total_seconds() / 3600)
                if c.sla and resolved_at <= as_utc(c.sla.deadline):
                    met += 1

        total = len(complaints)
        return {
            "total": total,
            "open": sum(by_status[s] for s in Status.OPEN),
            "overdue": overdue,
            "escalated": escalated,
            "resolved": resolved,
            "avg_resolution_hours": round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else None,
            "sla_compliance_percent": round(met / resolved * 100, 1) if resolved else None,
            "by_status": dict(by_status),
            "by_priority": dict(by_priority),
            "by_category": dict(by_category.most_common()),
            "trend": [{"date": d, "count": trend[d]} for d in sorted(trend)],
            "scope": "assigned" if user.role == Role.STAFF else "all",
            "generated_at": now,
        }
