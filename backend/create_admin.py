"""Create the first admin account (or reset an existing admin's password).

Usage:  python create_admin.py admin@clinic.com "Full Name"
The password is asked for interactively, so it never lands in shell history.
In Docker:  docker compose exec backend python create_admin.py admin@clinic.com "Full Name"
"""

import getpass
import sys

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Role, User
from app.security import hash_password


def main(email: str, full_name: str) -> None:
    password = getpass.getpass("Password (min 8 characters): ")
    if len(password) < 8:
        sys.exit("Password too short.")
    if getpass.getpass("Repeat password: ") != password:
        sys.exit("Passwords don't match.")

    email = email.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user and user.role != Role.admin:
            sys.exit(f"{email} exists with role {user.role.value}; change it in the app instead.")
        if user:
            user.password_hash, user.is_active = hash_password(password), True
            print(f"Password reset for admin {email}.")
        else:
            db.add(User(email=email, full_name=full_name, role=Role.admin, password_hash=hash_password(password)))
            print(f"Admin {email} created.")
        db.commit()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
