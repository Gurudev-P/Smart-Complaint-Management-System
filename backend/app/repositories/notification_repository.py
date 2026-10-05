import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from backend.app.models import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, notification: Notification) -> Notification:
        self.db.add(notification)
        return notification

    def get(self, notification_id: uuid.UUID) -> Notification | None:
        return self.db.get(Notification, notification_id)

    def list_for(
        self,
        recipient_id: uuid.UUID,
        unread_only: bool,
        limit: int,
        event_type: str | None = None,
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.recipient_id == recipient_id)

        if unread_only:
            stmt = stmt.where(Notification.read_status.is_(False))

        if event_type:
            stmt = stmt.where(Notification.event_type == event_type)

        return list(self.db.scalars(stmt.order_by(Notification.created_at.desc()).limit(limit)))

    def unread_count(self, recipient_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Notification).where(Notification.recipient_id == recipient_id, Notification.read_status.is_(False))
        return self.db.scalar(stmt) or 0

    def mark_all_read(self, recipient_id: uuid.UUID) -> int:
        result = self.db.execute(update(Notification).where(Notification.recipient_id == recipient_id, Notification.read_status.is_(False)).values(read_status=True))
        return result.rowcount or 0

    def exists(self, complaint_id: uuid.UUID, event_type: str) -> bool:
        stmt = select(func.count()).select_from(Notification).where(Notification.complaint_id == complaint_id, Notification.event_type == event_type)
        return (self.db.scalar(stmt) or 0) > 0
