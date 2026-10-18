"""Role matrix from docs/roles.md, checked endpoint by endpoint."""

import re
from datetime import date, datetime, timedelta

import pytest

from app.booking import CLINIC_TZ
from app.main import app
from app.models import Role

API = "/api/v1"
DAY = date.today() + timedelta(days=7)
HOURS = [{"day_of_week": d, "start_time": "09:00", "end_time": "17:00"} for d in range(7)]


def at(h, m=0):
    return datetime(DAY.year, DAY.month, DAY.day, h, m, tzinfo=CLINIC_TZ).isoformat()


def test_everything_but_health_and_login_needs_a_token(anon):
    assert anon.get("/health").status_code == 200
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith(API) or path == f"{API}/auth/login":
            continue
        url = re.sub(r"\{[^}]+\}", "1", path)
        for method in route.methods - {"HEAD", "OPTIONS"}:
            r = anon.request(method, url)
            assert r.status_code == 401, f"{method} {path} -> {r.status_code}"


@pytest.fixture
def world(client):
    """Admin-created data: two dentists (one linked to a dentist login), a patient, one appointment each."""
    pid = client.post(f"{API}/patients", json={"first_name": "Mya", "last_name": "Win", "phone": "09-123"}).json()["id"]
    pid2 = client.post(f"{API}/patients", json={"first_name": "Ko", "last_name": "Zaw", "phone": "09-456"}).json()["id"]
    other = client.post(f"{API}/dentists", json={"full_name": "Dr. Other"}).json()["id"]
    return {"client": client, "patient": pid, "patient2": pid2, "other_dentist": other}


@pytest.fixture
def dentist_client(client_for, world):
    c = client_for(Role.dentist, dentist=True)
    admin = world["client"]
    own = next(d["id"] for d in admin.get(f"{API}/dentists").json() if d["user_id"] == c.user.id)
    for d in (own, world["other_dentist"]):
        admin.put(f"{API}/dentists/{d}/availability", json=HOURS)

    def book(dentist, patient):
        r = admin.post(f"{API}/appointments", json={"patient_id": patient, "dentist_id": dentist,
                                                    "start_at": at(10), "end_at": at(10, 30)})
        assert r.status_code == 201, r.text
        return r.json()["id"]

    world |= {"own_dentist": own, "own_appt": book(own, world["patient"]),
              "other_appt": book(world["other_dentist"], world["patient2"])}
    return c


@pytest.mark.parametrize("role", [Role.receptionist, Role.dentist])
def test_admin_only_endpoints(client_for, role):
    c = client_for(role, dentist=role == Role.dentist)
    for url in ("/users", "/audit-logs", f"/reports/rates?date_from={DAY}&date_to={DAY}"):
        assert c.get(API + url).status_code == 403, url
    assert c.post(f"{API}/users", json={"email": "x@example.com", "full_name": "X", "role": "admin",
                                        "password": "password-123"}).status_code == 403
    assert c.post(f"{API}/dentists", json={"full_name": "Dr. X"}).status_code == 403
    assert c.put(f"{API}/dentists/1/availability", json=HOURS).status_code == 403


def test_receptionist_runs_the_front_desk(client_for, world):
    c = client_for(Role.receptionist)
    d = world["other_dentist"]
    world["client"].put(f"{API}/dentists/{d}/availability", json=HOURS)
    assert c.post(f"{API}/patients", json={"first_name": "A", "last_name": "B", "phone": "09-777"}).status_code == 201
    assert c.patch(f"{API}/patients/{world['patient']}", json={"address": "Yangon"}).status_code == 200
    r = c.post(f"{API}/appointments", json={"patient_id": world["patient"], "dentist_id": d,
                                            "start_at": at(11), "end_at": at(11, 30)})
    assert r.status_code == 201
    appt = r.json()
    assert appt["created_by"] == c.user.id  # audit trail has the real user now
    assert c.post(f"{API}/appointments/{appt['id']}/reschedule",
                  json={"start_at": at(12), "end_at": at(12, 30)}).status_code == 200
    assert c.post(f"{API}/appointments/{appt['id']}/cancel").status_code == 200
    # time off is clinic scheduling: admin only (docs/api.md)
    assert c.post(f"{API}/dentists/{d}/time-off", json={"start_at": at(15), "end_at": at(16)}).status_code == 403

    logs = world["client"].get(f"{API}/audit-logs", params={"entity_id": appt["id"]}).json()
    assert {log["user_id"] for log in logs} == {c.user.id}


def test_dentist_reads_but_does_not_book(dentist_client, world):
    c = dentist_client
    assert c.get(f"{API}/patients").status_code == 200
    assert c.get(f"{API}/dentists").status_code == 200
    assert c.post(f"{API}/patients", json={"first_name": "A", "last_name": "B", "phone": "09-777"}).status_code == 403
    assert c.patch(f"{API}/patients/{world['patient']}", json={"address": "x"}).status_code == 403
    assert c.post(f"{API}/appointments", json={"patient_id": world["patient"], "dentist_id": world["own_dentist"],
                                               "start_at": at(14), "end_at": at(14, 30)}).status_code == 403
    assert c.post(f"{API}/appointments/{world['own_appt']}/cancel").status_code == 403
    assert c.post(f"{API}/appointments/{world['own_appt']}/reschedule",
                  json={"start_at": at(14), "end_at": at(14, 30)}).status_code == 403
    assert c.post(f"{API}/dentists/{world['own_dentist']}/time-off",
                  json={"start_at": at(15), "end_at": at(16)}).status_code == 403


def test_dentist_sees_only_own_patients(dentist_client, world, client_for):
    c = dentist_client
    page = c.get(f"{API}/patients").json()
    assert [p["id"] for p in page["items"]] == [world["patient"]] and page["total"] == 1
    assert c.get(f"{API}/patients", params={"q": "Zaw"}).json()["total"] == 0
    assert c.get(f"{API}/patients/{world['patient']}").status_code == 200
    # another dentist's patient looks like it doesn't exist
    assert c.get(f"{API}/patients/{world['patient2']}").status_code == 404
    # staff still see everyone
    assert world["client"].get(f"{API}/patients").json()["total"] == 2
    unlinked = client_for(Role.dentist, email="unlinked@test.local")
    assert unlinked.get(f"{API}/patients").status_code == 403


def test_dentist_sees_only_own_appointments(dentist_client, world):
    c = dentist_client
    page = c.get(f"{API}/appointments").json()
    assert [a["id"] for a in page["items"]] == [world["own_appt"]]
    assert c.get(f"{API}/appointments", params={"dentist_id": world["other_dentist"]}).status_code == 403
    assert c.get(f"{API}/appointments/{world['own_appt']}").status_code == 200
    assert c.get(f"{API}/appointments/{world['other_appt']}").status_code == 404
    assert c.patch(f"{API}/appointments/{world['other_appt']}", json={"notes": "x"}).status_code == 404


def test_dentist_updates_own_notes_and_status(dentist_client, world):
    c, appt = dentist_client, world["own_appt"]
    r = c.patch(f"{API}/appointments/{appt}", json={"notes": "Filling done, review in 6 months"})
    assert r.status_code == 200 and r.json()["notes"].startswith("Filling")
    assert c.patch(f"{API}/appointments/{appt}", json={"reason": "changed"}).status_code == 403
    assert c.patch(f"{API}/appointments/{appt}", json={"status": "cancelled"}).status_code == 403
    # completed/no-show are allowed for dentists, but the booking rules still apply (appointment is in the future)
    r = c.patch(f"{API}/appointments/{appt}", json={"status": "completed"})
    assert r.status_code == 409 and r.json()["code"] == "too_early"


def test_unlinked_dentist_account_gets_clear_error(client_for):
    c = client_for(Role.dentist)  # no Dentist row linked yet
    r = c.get(f"{API}/appointments")
    assert r.status_code == 403 and "not linked" in r.json()["detail"]
