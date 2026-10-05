"""Notification Service (FR-20, FR-21).

In-app notifications are the baseline channel. External channels are pluggable adapters;
none is enabled by default, so provider credentials never need to live in the codebase.
"""

import logging
import uuid
from typing import Protocol

from sqlalchemy.orm import Session

from backend.app.core.constants import Channel, Role
from backend.app.core.errors import Forbidden, NotFound
from backend.app.models import Notification, User
from backend.app.repositories.notification_repository import NotificationRepository
from backend.app.repositories.user_repository import UserRepository

log = logging.getLogger(__name__)


class ExternalChannelAdapter(Protocol):
    channel: str

    def send(self, recipient: User, message: str) -> None: ...


_external_adapters: list[ExternalChannelAdapter] = []


def register_adapter(adapter: ExternalChannelAdapter) -> None:
    """Register an external channel (email/SMS/WhatsApp) adapter at startup."""
    _external_adapters.append(adapter)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)
        self.users = UserRepository(db)

    def notify(
        self,
        recipient_id: uuid.UUID,
        event_type: str,
        message: str,
        complaint_id: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            recipient_id=recipient_id,
            complaint_id=complaint_id,
            event_type=event_type,
            message=message,
            channel=Channel.IN_APP,
            read_status=False,
        )
        self.repo.add(notification)
        if _external_adapters:
            recipient = self.users.get(recipient_id)
            for adapter in _external_adapters:
                try:
                    adapter.send(recipient, message)
                except Exception:  # an external outage must never break the main workflow
                    log.exception("External notification via %s failed", adapter.channel)
        return notification

    def notify_admins(self, event_type: str, message: str, complaint_id: uuid.UUID | None = None) -> int:
        admins = self.users.list(role=Role.ADMIN, status="ACTIVE")
        for admin in admins:
            self.notify(admin.user_id, event_type, message, complaint_id)
        return len(admins)

    def list_for(
        self,
        user: User,
        unread_only: bool = False,
        limit: int = 50,
        event_type: str | None = None,
    ):
        return (
            self.repo.list_for(
                user.user_id,
                unread_only,
                limit,
                event_type,
            ),
            self.repo.unread_count(user.user_id),
        )

    def mark_read(self, user: User, notification_id: uuid.UUID) -> Notification:
        notification = self.repo.get(notification_id)
        if notification is None:
            raise NotFound("Notification not found")
        if notification.recipient_id != user.user_id:
            raise Forbidden("You can only update your own notifications")
        notification.read_status = True
        self.db.commit()
        return notification

    def mark_all_read(self, user: User) -> int:
        count = self.repo.mark_all_read(user.user_id)
        self.db.commit()
        return count
