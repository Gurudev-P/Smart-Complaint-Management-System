"""Load demo data: python -m backend.app.seed

Creates an administrator, two staff members, a user and default categories if they do not exist.
Intended for local development and demonstrations only.
"""
from backend.app.core.constants import Role
from backend.app.db.session import SessionLocal
from backend.app.models import Category
from backend.app.repositories.category_repository import CategoryRepository
from backend.app.repositories.sla_rule_repository import SLARuleRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.services.auth_service import AuthService

DEMO_USERS = [
    ("Admin User", "admin@scms.example.com", "Admin@1234", Role.ADMIN),
    ("Ravi Staff", "staff1@scms.example.com", "Staff@1234", Role.STAFF),
    ("Meena Staff", "staff2@scms.example.com", "Staff@1234", Role.STAFF),
    ("Asha User", "user@scms.example.com", "User@1234", Role.USER),
]
DEMO_CATEGORIES = [
    ("IT & Network", "Wi-Fi, lab computers, portal access"),
    ("Infrastructure", "Classrooms, furniture, electrical, plumbing"),
    ("Hostel", "Rooms, mess, housekeeping"),
    ("Academics", "Timetable, examinations, course registration"),
    ("Transport", "Bus routes, timings, parking"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        SLARuleRepository(db).ensure_defaults()
        auth, users, categories = AuthService(db), UserRepository(db), CategoryRepository(db)
        auth.ensure_system_user()
        for name, email, password, role in DEMO_USERS:
            if users.get_by_email(email) is None:
                auth.register(name, email, password, role)
        for name, description in DEMO_CATEGORIES:
            if categories.get_by_name(name) is None:
                categories.add(Category(name=name, description=description, active_flag=True))
        db.commit()
        print("Demo data ready. Logins:")
        for _, email, password, role in DEMO_USERS:
            print(f"  {role:<6} {email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
