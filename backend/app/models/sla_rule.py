import uuid

from sqlalchemy import UUID, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class SLARule(Base):
    """Configurable SLA target per priority level (FR-16, BR-06)."""

    __tablename__ = "sla_rules"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
    )

    # Target resolution duration in minutes.
    target_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Percentage of the SLA duration after which a complaint counts as "approaching" (FR-17).
    approaching_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=80,
    )
