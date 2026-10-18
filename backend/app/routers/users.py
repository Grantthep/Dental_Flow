"""Staff accounts. Admin only."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_roles
from app.models import Role, User
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import hash_password, password_changed_now

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_roles(Role.admin))])


def _get_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


def _active_admins(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role == Role.admin, User.is_active))


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.full_name)).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    user = User(email=body.email.lower(), full_name=body.full_name, role=body.role,
                password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "A user with this email already exists")
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db)):
    user = _get_or_404(db, user_id)
    changes = body.model_dump(exclude_unset=True)
    loses_admin = user.role == Role.admin and user.is_active and (
        changes.get("role", Role.admin) != Role.admin or changes.get("is_active") is False
    )
    if loses_admin and _active_admins(db) <= 1:
        raise HTTPException(409, "Cannot remove the last active admin")
    if "password" in changes:
        user.password_hash = hash_password(changes.pop("password"))
        user.password_changed_at = password_changed_now()
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
