import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Resolution(Base):
    __tablename__ = "resolutions"

    resolution_id: Mapped[uuid.UUID] = mapped_column(
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

    resolver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    resolution_details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="resolution",
    )

    resolver: Mapped["User"] = relationship(
        "User",
    )