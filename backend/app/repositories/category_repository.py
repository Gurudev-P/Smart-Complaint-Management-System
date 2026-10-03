import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, category_id: uuid.UUID) -> Category | None:
        return self.db.get(Category, category_id)

    def get_by_name(self, name: str) -> Category | None:
        return self.db.scalar(select(Category).where(func.lower(Category.name) == name.lower()))

    def list(self, include_inactive: bool = False) -> list[Category]:
        stmt = select(Category).order_by(Category.name)
        if not include_inactive:
            stmt = stmt.where(Category.active_flag.is_(True))
        return list(self.db.scalars(stmt))

    def add(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        return category
