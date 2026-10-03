import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.category_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SUBMITTED",
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    creator: Mapped["User"] = relationship(
        "User",
        back_populates="complaints",
    )

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="complaints",
    )

    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="complaint",
    )

    status_history: Mapped[list["StatusHistory"]] = relationship(
        "StatusHistory",
        back_populates="complaint",
    )

    sla: Mapped["SLA | None"] = relationship(
        "SLA",
        back_populates="complaint",
        uselist=False,
    )

    resolution: Mapped["Resolution | None"] = relationship(
        "Resolution",
        back_populates="complaint",
        uselist=False,
    )