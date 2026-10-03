import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class SLA(Base):
    __tablename__ = "sla"

    sla_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.complaint_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Stored as minutes in the baseline implementation.
    target_duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    escalation_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="sla",
    )