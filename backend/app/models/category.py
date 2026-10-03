import uuid

from sqlalchemy import UUID, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    active_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    complaints: Mapped[list["Complaint"]] = relationship(
        "Complaint",
        back_populates="category",
    )