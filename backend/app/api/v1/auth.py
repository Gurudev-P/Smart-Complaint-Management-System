from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models import User
from backend.app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """FR-01: self-registration always creates a USER account."""
    return AuthService(db).register(body.name, body.email, body.password)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """FR-02 / FR-04: returns a bearer token, or a generic 401 for bad credentials."""
    token, user = AuthService(db).authenticate(body.email, body.password)
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: User = Depends(get_current_user)):
    """Tokens are stateless; the client discards its token. Kept for API completeness."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
