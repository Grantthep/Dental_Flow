import os

# Point the app at the test database before app.db is imported.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/dentalflow_test"
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402,F401
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Dentist, Role, User  # noqa: E402
from app.ratelimit import login_limiter  # noqa: E402
from app.security import create_access_token, hash_password  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    login_limiter.reset()
    yield


@pytest.fixture
def make_user():
    """make_user(role, email=None, dentist=False) -> User; dentist=True also creates a linked Dentist row."""
    def make(role: Role, email: str | None = None, dentist: bool = False) -> User:
        with SessionLocal() as s:
            user = User(email=email or f"{role.value}@test.local", full_name=f"Test {role.value}",
                        role=role, password_hash=hash_password(PASSWORD))
            s.add(user)
            s.flush()
            if dentist:
                s.add(Dentist(full_name=f"Dr. {role.value}", user_id=user.id))
            s.commit()
            return user
    return make


@pytest.fixture
def client_for(make_user):
    """client_for(role) -> TestClient sending a valid token for a new user with that role."""
    def make(role: Role, **kw) -> TestClient:
        user = make_user(role, **kw)
        c = TestClient(app)
        c.headers["Authorization"] = f"Bearer {create_access_token(user.id, role.value)}"
        c.user = user
        return c
    return make


@pytest.fixture
def client(client_for):
    """Logged in as admin (can do everything), so feature tests don't need to think about auth."""
    return client_for(Role.admin, email="admin@test.local")


@pytest.fixture
def anon():
    return TestClient(app)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session
