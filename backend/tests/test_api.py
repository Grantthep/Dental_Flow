from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Appointment, AppointmentStatus, Dentist, Patient

PATIENT = {"first_name": "Mya", "last_name": "Win", "phone": "09-123-456-789"}


def test_patient_crud_and_search(client):
    r = client.post("/api/v1/patients", json=PATIENT)
    assert r.status_code == 201
    pid = r.json()["id"]
    client.post("/api/v1/patients", json={**PATIENT, "first_name": "Ko", "last_name": "Zaw", "phone": "09-999"})

    assert client.get("/api/v1/patients", params={"q": "mya win"}).json()["total"] == 1
    assert client.get("/api/v1/patients", params={"q": "09-123"}).json()["total"] == 1
    assert client.get("/api/v1/patients").json()["total"] == 2

    r = client.patch(f"/api/v1/patients/{pid}", json={"is_active": False})
    assert r.json()["is_active"] is False
    assert client.get("/api/v1/patients").json()["total"] == 1
    assert client.get("/api/v1/patients/9999").status_code == 404


@pytest.mark.parametrize(
    "bad", [{"first_name": ""}, {"phone": "abc"}, {"email": "not-an-email"}, {"phone": None}]
)
def test_patient_validation(client, bad):
    assert client.post("/api/v1/patients", json={**PATIENT, **bad}).status_code == 422


def test_dentist_crud(client):
    r = client.post("/api/v1/dentists", json={"full_name": "Dr. Test"})
    assert r.status_code == 201
    did = r.json()["id"]
    assert client.patch(f"/api/v1/dentists/{did}", json={"specialty": "Ortho"}).json()["specialty"] == "Ortho"
    assert client.patch(f"/api/v1/dentists/{did}", json={"user_id": 999}).status_code == 409
    assert len(client.get("/api/v1/dentists").json()) == 1


def test_db_blocks_double_booking(db):
    dentist, p1, p2 = Dentist(full_name="Dr. A"), Patient(**PATIENT), Patient(**PATIENT)
    db.add_all([dentist, p1, p2])
    db.commit()
    t = datetime(2030, 1, 1, 9, tzinfo=UTC)

    def book(patient, start, mins=30, status=AppointmentStatus.booked):
        db.add(Appointment(patient_id=patient.id, dentist_id=dentist.id, start_at=start,
                           end_at=start + timedelta(minutes=mins), status=status))
        db.commit()

    book(p1, t)
    book(p2, t + timedelta(minutes=30))  # back-to-back is fine
    with pytest.raises(IntegrityError, match="ex_appointments_dentist_overlap"):
        book(p2, t + timedelta(minutes=15))
    db.rollback()

    # a cancelled appointment frees the slot
    db.query(Appointment).filter_by(patient_id=p1.id).update({"status": AppointmentStatus.cancelled})
    db.commit()
    book(p2, t - timedelta(minutes=15), mins=30)
