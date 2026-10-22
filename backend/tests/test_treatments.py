from datetime import timedelta

import pytest
from sqlalchemy import update

from app.models import Appointment, AppointmentStatus, Role
from tests.test_permissions import API, dentist_client, world  # noqa: F401  (fixtures)


@pytest.fixture
def past(db, world, dentist_client):  # noqa: F811
    """Move both appointments 8 days back, so they have happened."""
    db.execute(update(Appointment).values(start_at=Appointment.start_at - timedelta(days=8),
                                          end_at=Appointment.end_at - timedelta(days=8)))
    db.commit()
    return world


def add(c, appt, **body):
    return c.post(f"{API}/appointments/{appt}/treatments", json={"procedure": "Filling", **body})


def test_add_and_history(client, past):
    a = past["own_appt"]
    r = add(client, a, tooth="36", notes="Composite, 2 surfaces")
    assert r.status_code == 201, r.text
    assert r.json()["appointment"]["dentist"]["id"] == past["own_dentist"] and r.json()["created_by"] == client.user.id
    add(client, a, procedure="Scaling")

    assert [t["procedure"] for t in client.get(f"{API}/appointments/{a}/treatments").json()] == ["Filling", "Scaling"]
    history = client.get(f"{API}/patients/{past['patient']}/treatments").json()
    assert len(history) == 2 and history[0]["procedure"] == "Scaling"  # newest first
    assert client.get(f"{API}/patients/{past['patient2']}/treatments").json() == []
    logs = client.get(f"{API}/audit-logs", params={"entity_type": "treatment"}).json()
    assert len(logs) == 2


@pytest.mark.parametrize("body", [{"procedure": ""}, {"tooth": "9"}, {"tooth": "36a"}, {"tooth": "19"}])
def test_validation(client, past, body):
    assert add(client, past["own_appt"], **body).status_code == 422


def test_not_before_start_or_on_cancelled(client, world, dentist_client, db):  # noqa: F811
    r = add(client, world["own_appt"])  # still in the future
    assert r.status_code == 409 and r.json()["code"] == "too_early"
    db.execute(update(Appointment).values(start_at=Appointment.start_at - timedelta(days=8),
                                          end_at=Appointment.end_at - timedelta(days=8),
                                          status=AppointmentStatus.cancelled))
    db.commit()
    r = add(client, world["own_appt"])
    assert r.status_code == 409 and r.json()["code"] == "bad_status"


def test_append_only(client, past):
    tid = add(client, past["own_appt"]).json()["id"]
    for method in ("PATCH", "PUT", "DELETE"):
        assert client.request(method, f"{API}/appointments/{past['own_appt']}/treatments/{tid}").status_code in (404, 405)


def test_permissions(client_for, dentist_client, past):  # noqa: F811
    own, other = past["own_appt"], past["other_appt"]
    assert add(dentist_client, own).status_code == 201
    assert add(dentist_client, other).status_code == 404       # other dentist's appointment is invisible
    assert dentist_client.get(f"{API}/appointments/{other}/treatments").status_code == 404
    assert dentist_client.get(f"{API}/patients/{past['patient']}/treatments").status_code == 200   # own patient
    assert dentist_client.get(f"{API}/patients/{past['patient2']}/treatments").status_code == 404  # not theirs

    reception = client_for(Role.receptionist)
    assert add(reception, own).status_code == 403
    assert reception.get(f"{API}/appointments/{own}/treatments").status_code == 200
    assert reception.get(f"{API}/patients/{past['patient']}/treatments").status_code == 200
