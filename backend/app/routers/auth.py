from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import User
from app.ratelimit import login_limiter
from app.schemas import PasswordChange, Token, UserOut
from app.security import ACCESS_TOKEN_MINUTES, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password form: `username` = email. Logout is client-side (drop the token)."""
    email = form.username.strip().lower()
    # Per IP + email, so one person mistyping doesn't lock out the whole front desk.
    key = f"{request.client.host if request.client else '?'}|{email}"
    if wait := login_limiter.retry_after(key):
        raise HTTPException(429, "Too many failed logins, try again later", headers={"Retry-After": str(wait)})

    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if not verify_password(form.password, user.password_hash if user else None) or not user.is_active:
        login_limiter.fail(key)
        raise HTTPException(401, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})

    login_limiter.reset(key)
    return Token(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=ACCESS_TOKEN_MINUTES * 60,
        user=user,
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post("/change-password", status_code=204)
def change_password(body: PasswordChange, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    db.commit()
