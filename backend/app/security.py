"""Password hashing (Argon2) and JWT access tokens."""

import os
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

APP_ENV = os.getenv("APP_ENV", "development")
_DEV_SECRET = "dev-only-insecure-secret-change-me"
SECRET_KEY = os.getenv("SECRET_KEY", _DEV_SECRET)
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))  # one clinic shift

if APP_ENV != "development" and (SECRET_KEY == _DEV_SECRET or len(SECRET_KEY) < 32):
    raise RuntimeError("Set SECRET_KEY to a random value of at least 32 characters outside development")

_hasher = PasswordHash.recommended()
# Verified against when the email is unknown, so a wrong email takes as long as a wrong password.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False
    return _hasher.verify(password, password_hash)


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> tuple[int, int] | None:
    """(user id, issued-at unix seconds) from a valid, unexpired token; None otherwise."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require": ["sub", "exp", "iat"]})
        return int(payload["sub"]), int(payload["iat"])
    except (jwt.InvalidTokenError, ValueError):
        return None


def password_changed_now() -> datetime:
    """Stored in users.password_changed_at. Whole seconds, because a token's iat is whole seconds:
    a token issued later in the same second must still count as newer."""
    return datetime.now(UTC).replace(microsecond=0)
