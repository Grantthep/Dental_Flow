"""Hostile input: SQL injection and fuzzing. The API must answer 4xx (or a normal 2xx), never 500 or leak data."""

import pytest

from app.models import Role

API = "/api/v1"

SQLI = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "'; DROP TABLE patients; --",
    "\" OR \"\"=\"",
    "1; SELECT pg_sleep(5)",
    "%' UNION SELECT email, password_hash FROM users --",
    "\\'; --",
    "%",
    "_",
]

# Strings that tend to break parsers, encoders or the database driver.
JUNK = ["", " ", "a" * 10_000, "\x00", "nul\x00byte", "😀🦷", "‮", "<script>alert(1)</script>",
        "../../etc/passwd", "${jndi:ldap://x}", "-1", "1e309", "NaN", "null", "[]", "{}"]


@pytest.fixture
def patients(client):
    for first, last, phone in [("Mya", "Win", "09-111111"), ("Ko", "Zaw", "09-222222")]:
        assert client.post(f"{API}/patients", json={"first_name": first, "last_name": last, "phone": phone}).status_code == 201
    return client


@pytest.mark.parametrize("payload", SQLI)
def test_patient_search_is_not_injectable(patients, payload):
    r = patients.get(f"{API}/patients", params={"q": payload})
    assert r.status_code == 200
    # "%" and "_" are LIKE wildcards inside a bound parameter: harmless, may match. Anything else matches nothing.
    if payload not in ("%", "_"):
        assert r.json()["total"] == 0
    assert patients.get(f"{API}/patients").json()["total"] == 2  # table still there, nothing changed


@pytest.mark.parametrize("payload", SQLI)
def test_login_is_not_injectable(anon, make_user, payload):
    make_user(Role.admin, email="admin@test.local")
    for username, password in [(payload, "x"), ("admin@test.local", payload), (payload, payload)]:
        r = anon.post(f"{API}/auth/login", data={"username": username, "password": password})
        assert r.status_code in (401, 422, 429), r.text
        assert "access_token" not in r.text


@pytest.mark.parametrize("payload", SQLI)
def test_filters_are_not_injectable(client, payload):
    for url, params in [
        (f"{API}/audit-logs", {"entity_type": payload}),
        (f"{API}/appointments", {"patient_id": payload}),
        (f"{API}/appointments", {"status": payload}),
        (f"{API}/appointments", {"date_from": payload}),
        (f"{API}/reports/appointments", {"date_from": payload}),
        (f"{API}/reports/rates", {"dentist_id": payload}),
    ]:
        r = client.get(url, params=params)
        assert r.status_code in (200, 404, 422), f"{url} {params} -> {r.status_code}"
        if r.status_code == 200 and isinstance(r.json(), list):
            assert r.json() == []


@pytest.mark.parametrize("payload", SQLI)
def test_path_ids_are_not_injectable(client, payload):
    for url in (f"{API}/patients/{payload}", f"{API}/appointments/{payload}", f"{API}/dentists/{payload}"):
        assert client.get(url).status_code in (404, 422)


@pytest.mark.parametrize("value", JUNK)
def test_fuzzed_patient_fields_never_500(client, value):
    base = {"first_name": "Mya", "last_name": "Win", "phone": "09-123456"}
    for field in ("first_name", "last_name", "phone", "email", "gender", "address", "medical_notes", "date_of_birth"):
        r = client.post(f"{API}/patients", json=base | {field: value})
        assert r.status_code in (201, 422), f"{field}={value[:20]!r} -> {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("value", JUNK + [None, 0, -1, 2**63, 1.5, True, [], {}])
def test_fuzzed_booking_fields_never_500(client, value):
    base = {"patient_id": 1, "dentist_id": 1, "start_at": "2030-01-01T10:00:00+06:30", "end_at": "2030-01-01T10:30:00+06:30"}
    for field in (*base, "reason"):
        r = client.post(f"{API}/appointments", json=base | {field: value})
        assert r.status_code < 500, f"{field}={value!r} -> {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("value", JUNK)
def test_fuzzed_search_and_login_never_500(patients, anon, value):
    assert patients.get(f"{API}/patients", params={"q": value}).status_code < 500
    assert anon.post(f"{API}/auth/login", data={"username": value, "password": value}).status_code < 500


@pytest.mark.parametrize("body", ["not json", "{", "[1,2", "\x00", '{"first_name": ' + "[" * 5000])
def test_malformed_json_is_rejected(client, body):
    r = client.post(f"{API}/patients", content=body, headers={"Content-Type": "application/json"})
    assert r.status_code in (400, 422)


def test_mass_assignment_is_ignored(client):
    # Unknown/privileged fields in the body must not change server-controlled columns.
    r = client.post(f"{API}/patients", json={"first_name": "A", "last_name": "B", "phone": "09-123456",
                                             "id": 999, "is_active": False, "created_at": "2000-01-01T00:00:00Z"})
    assert r.status_code == 201
    assert r.json()["id"] != 999


def test_cannot_grant_self_admin(client_for):
    c = client_for(Role.receptionist)
    assert c.patch(f"{API}/users/{c.user.id}", json={"role": "admin"}).status_code == 403
    assert c.get(f"{API}/auth/me").json()["role"] == "receptionist"


def test_errors_do_not_leak_internals(client):
    r = client.get(f"{API}/patients/abc")
    assert r.status_code == 422
    assert "Traceback" not in r.text and "sqlalchemy" not in r.text.lower()
