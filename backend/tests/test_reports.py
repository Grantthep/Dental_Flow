from datetime import datetime, timedelta

import pytest

from app.booking import CLINIC_TZ
from app.models import Appointment, AppointmentStatus as S, Dentist, Patient

API = "/api/v1/reports"


@pytest.fixture
def data(db):
    d1, d2, idle = Dentist(full_name="Dr. A"), Dentist(full_name="Dr. B"), Dentist(full_name="Dr. C")
    patients = [Patient(first_name=f"P{i}", last_name="X", phone="09-000-000") for i in range(6)]
    db.add_all([d1, d2, idle, *patients])
    db.commit()

    def appt(i, dentist, day, hh, mm, status, mins=30):
        start = datetime(2025, 3, day, hh, mm, tzinfo=CLINIC_TZ)  # Mon 3 Mar 2025 .. Mon 10 Mar
        db.add(Appointment(patient_id=patients[i].id, dentist_id=dentist.id, start_at=start,
                           end_at=start + timedelta(minutes=mins), status=status))

    appt(0, d1, 3, 9, 0, S.completed)
    appt(1, d1, 3, 10, 0, S.no_show)
    appt(2, d2, 3, 9, 0, S.cancelled)
    appt(3, d2, 4, 0, 15, S.completed, mins=60)  # 00:15 local = previous day in UTC
    appt(4, d1, 10, 9, 0, S.booked)              # next week
    appt(5, d1, 20, 9, 0, S.completed)           # outside the range used below
    db.commit()
    return {"d1": d1.id, "d2": d2.id}


RANGE = {"date_from": "2025-03-03", "date_to": "2025-03-10"}


def test_by_day_includes_empty_days_and_uses_clinic_tz(client, data):
    rows = client.get(f"{API}/appointments", params=RANGE).json()
    assert [r["period"] for r in rows][:2] == ["2025-03-03", "2025-03-04"] and len(rows) == 8
    by_day = {r["period"]: r for r in rows}
    assert by_day["2025-03-03"] == {"period": "2025-03-03", "total": 3, "completed": 1, "cancelled": 1,
                                         "no_show": 1, "upcoming": 0}
    assert by_day["2025-03-04"]["total"] == 1
    assert by_day["2025-03-05"]["total"] == 0
    assert by_day["2025-03-10"]["upcoming"] == 1


def test_by_week_and_dentist_filter(client, data):
    rows = client.get(f"{API}/appointments", params=RANGE | {"group_by": "week"}).json()
    assert [(r["period"], r["total"]) for r in rows] == [("2025-03-03", 4), ("2025-03-10", 1)]
    rows = client.get(f"{API}/appointments", params=RANGE | {"group_by": "week", "dentist_id": data["d2"]}).json()
    assert [r["total"] for r in rows] == [2, 0]


def test_per_dentist(client, data):
    rows = {r["full_name"]: r for r in client.get(f"{API}/dentists", params=RANGE).json()}
    assert rows["Dr. A"]["total"] == 3 and rows["Dr. A"]["booked_minutes"] == 60  # completed + booked; no-show excluded
    assert rows["Dr. B"]["cancelled"] == 1 and rows["Dr. B"]["booked_minutes"] == 60
    assert rows["Dr. C"]["total"] == 0


def test_rates(client, data):
    r = client.get(f"{API}/rates", params=RANGE).json()
    assert r["total"] == 5
    assert r["cancellation_rate"] == 0.2           # 1 / 5
    assert r["no_show_rate"] == round(1 / 3, 4)    # 1 / (2 completed + 1 no-show)
    empty = client.get(f"{API}/rates", params={"date_from": "2020-01-01", "date_to": "2020-01-31"}).json()
    assert empty["total"] == 0 and empty["no_show_rate"] is None


def test_bad_range(client):
    assert client.get(f"{API}/rates", params={"date_from": "2025-03-10", "date_to": "2025-03-01"}).status_code == 422
    assert client.get(f"{API}/rates", params={"date_from": "2020-01-01", "date_to": "2025-01-01"}).status_code == 422
    assert client.get(f"{API}/appointments", params=RANGE | {"group_by": "year"}).status_code == 422
