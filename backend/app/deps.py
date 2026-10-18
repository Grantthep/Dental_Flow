"""Auth dependencies: who is calling, and are they allowed. Role matrix: docs/roles.md."""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Dentist, Role, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

STAFF = (Role.admin, Role.receptionist)  # front-desk actions: patients, bookings


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user_id = decode_access_token(token)
    user = db.get(User, user_id) if user_id else None
    # Deactivated accounts lose access immediately, even with an unexpired token.
    if not user or not user.is_active:
        raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    return user


def current_user_id(user: User = Depends(current_user)) -> int:
    return user.id


def require_roles(*roles: Role):
    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "You don't have permission to do this")
        return user

    return check


def own_dentist_id(db: Session, user: User) -> int:
    """Dentist row linked to a dentist-role user; 403 if the account isn't linked yet."""
    dentist_id = db.scalar(select(Dentist.id).where(Dentist.user_id == user.id))
    if dentist_id is None:
        raise HTTPException(403, "Your account is not linked to a dentist profile")
    return dentist_id
