import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.constants import AccountStatus, Role
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.auth import UserCreateRequest, UserOut, UserUpdateRequest
from backend.app.services.auth_service import AuthService
from backend.app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserOut])
def list_users(
    role: str | None = Query(default=None, pattern="^(USER|STAFF|ADMIN)$"),
    account_status: str | None = Query(default=None, pattern="^(ACTIVE|INACTIVE)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Admins can list everyone; staff who may assign can list active staff (assignment picker)."""
    if user.role != Role.ADMIN:
        if not (ComplaintService(db).can_assign(user) and role == Role.STAFF):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to perform this action")
        account_status = AccountStatus.ACTIVE
    return [u for u in UserRepository(db).list(role=role, status=account_status) if u.role in Role.ALL]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_roles(Role.ADMIN))):
    return AuthService(db).register(body.name, body.email, body.password, role=body.role)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(Role.ADMIN)),
):
    return AuthService(db).update_user(admin, user_id, **body.model_dump(exclude_none=True))
