from datetime import date, datetime, time, timedelta

import pytest

from app.booking import CLINIC_TZ

API = "/api/v1"
MON = date.today() + timedelta(days=7 - date.today().weekday() + 7)  # a Monday 1-2 weeks ahead


def at(hh, mm=0, day=MON):
    return datetime.combine(day, time(hh, mm), CLINIC_TZ).isoformat()


@pytest.fixture
def setup(client):
    def patient(name):
        return client.post(f"{API}/patients", json={"first_name": name, "last_name": "X", "phone": "09-111-222"}).json()["id"]

    d1 = client.post(f"{API}/dentists", json={"full_name": "Dr. One"}).json()["id"]
    d2 = client.post(f"{API}/dentists", json={"full_name": "Dr. Two"}).json()["id"]
    hours = [{"day_of_week": d, "start_time": s, "end_time": e}
             for d in range(6) for s, e in (("09:00", "12:00"), ("13:00", "17:00"))]
    for d in (d1, d2):
        assert client.put(f"{API}/dentists/{d}/availability", json=hours).status_code == 200
    return {"d1": d1, "d2": d2, "p1": patient("A"), "p2": patient("B")}


def book(client, s, dentist, patient, start, end):
    return client.post(f"{API}/appointments", json={
        "dentist_id": s[dentist], "patient_id": s[patient], "start_at": start, "end_at": end})


def test_create_and_audit(client, setup):
    r = book(client, setup, "d1", "p1", at(9), at(9, 30))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "booked" and body["dentist"]["full_name"] == "Dr. One" and body["patient"]["first_name"] == "A"
    logs = client.get(f"{API}/audit-logs", params={"entity_type": "appointment", "entity_id": body["id"]}).json()
    assert [log["action"] for log in logs] == ["create"]


def test_conflicts(client, setup):
    assert book(client, setup, "d1", "p1", at(9), at(9, 30)).status_code == 201
    assert book(client, setup, "d1", "p2", at(9, 30), at(10)).status_code == 201  # back-to-back ok

    r = book(client, setup, "d1", "p2", at(9, 15), at(9, 45))
    assert r.status_code == 409 and r.json()["code"] == "slot_taken"
    r = book(client, setup, "d2", "p1", at(9, 15), at(9, 45))  # p1 already with d1
    assert r.status_code == 409 and r.json()["code"] == "patient_busy"


@pytest.mark.parametrize("start,end,status,code", [
    (at(12), at(12, 30), 409, "outside_hours"),         # lunch break
    (at(11, 45), at(13, 15), 409, "outside_hours"),     # spans the break
    (at(8, 30), at(9, 30), 409, "outside_hours"),       # before opening
    (at(10, day=MON + timedelta(days=6)), at(10, 30, day=MON + timedelta(days=6)), 409, "outside_hours"),  # Sunday
    (at(10, day=date.today() - timedelta(days=1)), at(10, 30, day=date.today() - timedelta(days=1)), 422, "in_past"),
])
def test_booking_rules(client, setup, start, end, status, code):
    r = book(client, setup, "d1", "p1", start, end)
    assert r.status_code == status and r.json()["code"] == code


def test_end_before_start_rejected(client, setup):
    assert book(client, setup, "d1", "p1", at(10), at(9)).status_code == 422


def test_time_off_and_slots(client, setup):
    d1 = setup["d1"]
    slots = client.get(f"{API}/dentists/{d1}/slots", params={"date": MON.isoformat()}).json()
    # 09-12 and 13-17 in 15-min steps, 30-min length: 11 + 15
    assert len(slots) == 26

    r = client.post(f"{API}/dentists/{d1}/time-off", json={"start_at": at(13), "end_at": at(17), "reason": "Course"})
    assert r.status_code == 201
    r = book(client, setup, "d1", "p1", at(14), at(14, 30))
    assert r.status_code == 409 and r.json()["code"] == "time_off"

    assert book(client, setup, "d1", "p1", at(9), at(9, 30)).status_code == 201
    slots = client.get(f"{API}/dentists/{d1}/slots", params={"date": MON.isoformat()}).json()
    # afternoon off; 9:00 and 9:15 starts overlap the booking -> 11 - 2
    assert len(slots) == 9
    assert datetime.fromisoformat(slots[0]["start_at"]) == datetime.fromisoformat(at(9, 30))

    time_off_id = client.get(f"{API}/dentists/{d1}/time-off").json()[0]["id"]
    assert client.delete(f"{API}/time-off/{time_off_id}").status_code == 204
    assert book(client, setup, "d1", "p1", at(14), at(14, 30)).status_code == 201


def test_reschedule_cancel_and_status(client, setup):
    a = book(client, setup, "d1", "p1", at(9), at(9, 30)).json()["id"]
    b = book(client, setup, "d1", "p2", at(10), at(10, 30)).json()["id"]

    r = client.post(f"{API}/appointments/{a}/reschedule", json={"start_at": at(10, 15), "end_at": at(10, 45)})
    assert r.status_code == 409 and r.json()["code"] == "slot_taken"
    r = client.post(f"{API}/appointments/{a}/reschedule", json={"start_at": at(9, 15), "end_at": at(9, 45)})
    assert r.status_code == 200  # overlapping its own old time is fine

    assert client.post(f"{API}/appointments/{b}/cancel").json()["status"] == "cancelled"
    assert book(client, setup, "d1", "p1", at(10), at(10, 30)).status_code == 201  # cancelled slot is free again
    # cancelled is final
    assert client.patch(f"{API}/appointments/{b}", json={"status": "booked"}).status_code == 409
    assert client.post(f"{API}/appointments/{b}/reschedule", json={"start_at": at(11), "end_at": at(11, 30)}).status_code == 409

    r = client.patch(f"{API}/appointments/{a}", json={"status": "confirmed", "notes": "Bring X-ray"})
    assert r.json()["status"] == "confirmed" and r.json()["notes"] == "Bring X-ray"
    actions = [log["action"] for log in client.get(f"{API}/audit-logs", params={"entity_id": a}).json()]
    assert actions == ["update", "reschedule", "create"]


def test_list_filters(client, setup):
    book(client, setup, "d1", "p1", at(9), at(9, 30))
    book(client, setup, "d2", "p2", at(9), at(9, 30))
    nxt = MON + timedelta(days=1)
    book(client, setup, "d1", "p2", at(9, day=nxt), at(9, 30, day=nxt))

    def count(**params):
        return client.get(f"{API}/appointments", params=params).json()["total"]

    assert count() == 3
    assert count(dentist_id=setup["d1"]) == 2
    assert count(date_from=at(0), date_to=at(0, day=nxt)) == 2
    assert count(status="cancelled") == 0
    page = client.get(f"{API}/appointments", params={"size": 2, "page": 2}).json()
    assert len(page["items"]) == 1


def test_availability_overlap_rejected(client, setup):
    bad = [{"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
           {"day_of_week": 0, "start_time": "11:00", "end_time": "14:00"}]
    assert client.put(f"{API}/dentists/{setup['d1']}/availability", json=bad).status_code == 422


def test_cannot_complete_future_appointment(client, setup):
    a = book(client, setup, "d1", "p1", at(9), at(9, 30)).json()["id"]
    for status in ("completed", "no_show"):
        r = client.patch(f"{API}/appointments/{a}", json={"status": status})
        assert r.status_code == 409 and r.json()["code"] == "too_early"
