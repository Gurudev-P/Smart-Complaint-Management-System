import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def list(self, role: str | None = None, status: str | None = None) -> list[User]:
        stmt = select(User).order_by(User.name)
        if role:
            stmt = stmt.where(User.role == role)
        if status:
            stmt = stmt.where(User.account_status == status)
        return list(self.db.scalars(stmt))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def count_by_role(self, role: str) -> int:
        return self.db.scalar(select(func.count()).select_from(User).where(User.role == role)) or 0
