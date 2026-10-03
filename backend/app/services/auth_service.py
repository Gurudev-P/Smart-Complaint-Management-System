"""Authentication Service (FR-01–FR-04, NFR-04–NFR-06)."""
import uuid

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import AccountStatus, Role
from backend.app.core.errors import Conflict, Forbidden, NotAuthenticated, NotFound, ValidationFailed
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models import User
from backend.app.repositories.user_repository import UserRepository

SYSTEM_EMAIL = "system@scms.local"
SYSTEM_ROLE = "SYSTEM"

# A real bcrypt hash used to keep login timing similar for unknown e-mail addresses.
_DUMMY_HASH = hash_password("timing-equaliser-1")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, name: str, email: str, password: str, role: str = Role.USER) -> User:
        if self.users.get_by_email(email):
            raise Conflict("An account with this email already exists")
        user = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
            account_status=AccountStatus.ACTIVE,
        )
        self.users.add(user)
        self.db.commit()
        return user

    def authenticate(self, email: str, password: str) -> tuple[str, User]:
        user = self.users.get_by_email(email)
        if user is None or user.role == SYSTEM_ROLE:
            verify_password(password, _DUMMY_HASH)
            raise NotAuthenticated("Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise NotAuthenticated("Invalid email or password")
        if user.account_status != AccountStatus.ACTIVE:
            raise Forbidden("This account is inactive. Contact an administrator.")
        return create_access_token(user.user_id, user.role), user

    # --- administration (Manage Users use case) ---
    def update_user(self, actor: User, user_id: uuid.UUID, *, name=None, role=None, account_status=None) -> User:
        user = self.users.get(user_id)
        if user is None or user.role == SYSTEM_ROLE:
            raise NotFound("User not found")
        if user.user_id == actor.user_id and (
            (role and role != Role.ADMIN) or account_status == AccountStatus.INACTIVE
        ):
            raise ValidationFailed("You cannot remove your own administrator access")
        if name:
            user.name = name.strip()
        if role:
            user.role = role
        if account_status:
            user.account_status = account_status
        self.db.commit()
        return user

    def ensure_system_user(self) -> User:
        user = self.users.get_by_email(SYSTEM_EMAIL)
        if user is None:
            user = User(
                name="System",
                email=SYSTEM_EMAIL,
                password_hash=hash_password(uuid.uuid4().hex + "A1"),
                role=SYSTEM_ROLE,
                account_status=AccountStatus.INACTIVE,
            )
            self.users.add(user)
            self.db.commit()
        return user

    def bootstrap_admin(self) -> User | None:
        if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD):
            return None
        if self.users.count_by_role(Role.ADMIN) > 0:
            return None
        existing = self.users.get_by_email(settings.ADMIN_EMAIL)
        if existing:
            existing.role = Role.ADMIN
            existing.account_status = AccountStatus.ACTIVE
            self.db.commit()
            return existing
        return self.register(settings.ADMIN_NAME, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD, Role.ADMIN)
