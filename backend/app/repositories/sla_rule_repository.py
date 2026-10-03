import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.constants import DEFAULT_APPROACHING_PERCENT, DEFAULT_SLA_MINUTES, Priority
from backend.app.models import SLARule


class SLARuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[SLARule]:
        order = {p: i for i, p in enumerate(reversed(Priority.ALL))}
        return sorted(self.db.scalars(select(SLARule)), key=lambda r: order.get(r.priority, 99))

    def get(self, rule_id: uuid.UUID) -> SLARule | None:
        return self.db.get(SLARule, rule_id)

    def for_priority(self, priority: str) -> SLARule | None:
        return self.db.scalar(select(SLARule).where(SLARule.priority == priority))

    def ensure_defaults(self) -> None:
        existing = {r.priority for r in self.db.scalars(select(SLARule))}
        for priority, minutes in DEFAULT_SLA_MINUTES.items():
            if priority not in existing:
                self.db.add(
                    SLARule(
                        priority=priority,
                        target_minutes=minutes,
                        approaching_percent=DEFAULT_APPROACHING_PERCENT,
                    )
                )
        self.db.flush()
