from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.models import Role, User
from app.ratelimit import LoginLimiter
from app.security import ALGORITHM, SECRET_KEY, create_access_token, hash_password, verify_password
from tests.conftest import PASSWORD

API = "/api/v1"


def login(c, email, password=PASSWORD):
    return c.post(f"{API}/auth/login", data={"username": email, "password": password})


def test_password_hashing():
    h = hash_password("s3cret-pass")
    assert h != "s3cret-pass" and h.startswith("$argon2")
    assert verify_password("s3cret-pass", h)
    assert not verify_password("wrong", h)
    assert not verify_password("anything", None)  # unknown user


def test_login_and_me(anon, make_user):
    make_user(Role.receptionist, email="desk@test.local")
    r = login(anon, "DESK@test.local ")  # email is case/space-insensitive
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["user"]["role"] == "receptionist"
    assert "password_hash" not in body["user"]

    me = anon.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "desk@test.local"


@pytest.mark.parametrize("email,password", [("desk@test.local", "wrong-password"), ("nobody@test.local", PASSWORD)])
def test_login_rejects_bad_credentials(anon, make_user, email, password):
    make_user(Role.receptionist, email="desk@test.local")
    r = login(anon, email, password)
    assert r.status_code == 401
    assert r.json()["detail"] == "Incorrect email or password"  # same message: don't reveal which emails exist


def test_inactive_user_cannot_login_or_use_token(anon, client_for, db):
    c = client_for(Role.receptionist)
    user = db.get(User, c.user.id)
    user.is_active = False
    db.commit()
    assert login(anon, user.email).status_code == 401
    assert c.get(f"{API}/patients").status_code == 401


@pytest.mark.parametrize("token", [
    "not-a-jwt",
    jwt.encode({"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)}, SECRET_KEY, algorithm=ALGORITHM),
    jwt.encode({"sub": "1", "exp": datetime.now(UTC) + timedelta(hours=1)}, "x" * 32 + "wrong-key", algorithm=ALGORITHM),
    jwt.encode({"sub": "1"}, SECRET_KEY, algorithm=ALGORITHM),  # no expiry
    jwt.encode({"sub": "1", "exp": datetime.now(UTC) + timedelta(hours=1)}, None, algorithm="none"),
])
def test_bad_tokens_rejected(anon, make_user, token):
    make_user(Role.admin)  # id 1 exists, so only the token itself can be the problem
    r = anon.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_for_deleted_user_rejected(anon):
    r = anon.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {create_access_token(999, 'admin')}"})
    assert r.status_code == 401


def test_login_rate_limit(anon, make_user):
    make_user(Role.receptionist, email="desk@test.local")
    for _ in range(5):
        assert login(anon, "desk@test.local", "wrong-password").status_code == 401
    r = login(anon, "desk@test.local")  # even the right password is blocked now
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0

    make_user(Role.dentist, email="doc@test.local")
    assert login(anon, "doc@test.local").status_code == 200  # other accounts unaffected


def test_limiter_window_expires(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.ratelimit.time.monotonic", lambda: now[0])
    lim = LoginLimiter(max_failures=2, window=60)
    lim.fail("k")
    lim.fail("k")
    assert lim.retry_after("k") == 60
    now[0] += 61
    assert lim.retry_after("k") == 0


def test_change_password(anon, client_for):
    c = client_for(Role.dentist)
    bad = c.post(f"{API}/auth/change-password", json={"current_password": "nope", "new_password": "new-password-1"})
    assert bad.status_code == 400
    too_short = c.post(f"{API}/auth/change-password", json={"current_password": PASSWORD, "new_password": "short"})
    assert too_short.status_code == 422
    ok = c.post(f"{API}/auth/change-password", json={"current_password": PASSWORD, "new_password": "new-password-1"})
    assert ok.status_code == 204
    assert login(anon, c.user.email).status_code == 401
    assert login(anon, c.user.email, "new-password-1").status_code == 200


def test_admin_manages_users(client, anon):
    r = client.post(f"{API}/users", json={"email": "New@Example.com", "full_name": "New Desk",
                                          "role": "receptionist", "password": "password-123"})
    assert r.status_code == 201
    uid = r.json()["id"]
    assert r.json()["email"] == "new@example.com"
    dup = client.post(f"{API}/users", json={"email": "new@example.com", "full_name": "Again",
                                            "role": "dentist", "password": "password-123"})
    assert dup.status_code == 409
    assert login(anon, "new@example.com", "password-123").status_code == 200

    # admin password reset
    assert client.patch(f"{API}/users/{uid}", json={"password": "reset-pass-456"}).status_code == 200
    assert login(anon, "new@example.com", "reset-pass-456").status_code == 200
    assert client.patch(f"{API}/users/{uid}", json={"is_active": False}).json()["is_active"] is False
    assert len(client.get(f"{API}/users").json()) == 2


def test_cannot_remove_last_admin(client):
    me = client.user.id
    assert client.patch(f"{API}/users/{me}", json={"role": "receptionist"}).status_code == 409
    assert client.patch(f"{API}/users/{me}", json={"is_active": False}).status_code == 409


def test_cors_allows_frontend_origin(anon):
    r = anon.options(f"{API}/auth/login", headers={"Origin": "http://localhost:3000",
                                                   "Access-Control-Request-Method": "POST"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
    r = anon.options(f"{API}/auth/login", headers={"Origin": "https://evil.example",
                                                   "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
