from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import audit
from app.booking import BookingError, check_bookable
from app.db import get_db
from app.deps import current_user_id
from app.models import Appointment, AppointmentStatus as S
from app.schemas import AppointmentCreate, AppointmentOut, AppointmentUpdate, Page, TimeRange

router = APIRouter(prefix="/appointments", tags=["appointments"])

# Allowed status changes; completed / cancelled / no_show are final.
TRANSITIONS = {
    S.booked: {S.confirmed, S.completed, S.cancelled, S.no_show},
    S.confirmed: {S.completed, S.cancelled, S.no_show},
}
TRACKED = ("start_at", "end_at", "status", "reason", "notes")


def _snapshot(appt: Appointment, fields=TRACKED) -> dict:
    return {f: getattr(appt, f) for f in fields}


def _get_or_404(db: Session, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(404, "Appointment not found")
    return appt


def _commit(db: Session):
    # Two requests can pass check_bookable at the same moment; the exclusion constraint catches the loser.
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "overlap" in str(e.orig):
            raise BookingError(409, "slot_taken", "This time was just booked by someone else")
        raise


def _set_status(appt: Appointment, new: S):
    if new != appt.status and new not in TRANSITIONS.get(appt.status, set()):
        raise BookingError(409, "bad_status", f"Cannot change status from {appt.status.value} to {new.value}")
    if new in (S.completed, S.no_show) and appt.start_at > datetime.now(UTC):
        raise BookingError(409, "too_early", f"Cannot mark as {new.value} before the appointment starts")
    appt.status = new


@router.get("", response_model=Page[AppointmentOut])
def list_appointments(
    date_from: datetime | None = Query(None, description="start_at >= this"),
    date_to: datetime | None = Query(None, description="start_at < this"),
    dentist_id: int | None = None,
    patient_id: int | None = None,
    status: list[S] | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Appointment)
    if date_from:
        stmt = stmt.where(Appointment.start_at >= date_from)
    if date_to:
        stmt = stmt.where(Appointment.start_at < date_to)
    if dentist_id:
        stmt = stmt.where(Appointment.dentist_id == dentist_id)
    if patient_id:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    if status:
        stmt = stmt.where(Appointment.status.in_(status))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Appointment.start_at, Appointment.id).offset((page - 1) * size).limit(size)).all()
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(body: AppointmentCreate, db: Session = Depends(get_db), user_id=Depends(current_user_id)):
    check_bookable(db, body.dentist_id, body.patient_id, body.start_at, body.end_at)
    appt = Appointment(**body.model_dump(), created_by=user_id)
    db.add(appt)
    db.flush()
    audit(db, user_id, "create", "appointment", appt.id, after=_snapshot(appt, ("start_at", "end_at", "reason")))
    _commit(db)
    db.refresh(appt)
    return appt


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, appointment_id)


@router.patch("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int, body: AppointmentUpdate, db: Session = Depends(get_db), user_id=Depends(current_user_id)
):
    appt = _get_or_404(db, appointment_id)
    changes = body.model_dump(exclude_unset=True)
    before = _snapshot(appt, changes)
    if "status" in changes:
        _set_status(appt, changes.pop("status"))
    for field, value in changes.items():
        setattr(appt, field, value)
    audit(db, user_id, "update", "appointment", appt.id, before, _snapshot(appt, before))
    _commit(db)
    db.refresh(appt)
    return appt


@router.post("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(
    appointment_id: int, body: TimeRange, db: Session = Depends(get_db), user_id=Depends(current_user_id)
):
    appt = _get_or_404(db, appointment_id)
    if appt.status not in TRANSITIONS:
        raise BookingError(409, "bad_status", f"Cannot reschedule a {appt.status.value} appointment")
    check_bookable(db, appt.dentist_id, appt.patient_id, body.start_at, body.end_at, exclude_id=appt.id)
    before = _snapshot(appt, ("start_at", "end_at"))
    appt.start_at, appt.end_at = body.start_at, body.end_at
    audit(db, user_id, "reschedule", "appointment", appt.id, before, _snapshot(appt, before))
    _commit(db)
    db.refresh(appt)
    return appt


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), user_id=Depends(current_user_id)):
    appt = _get_or_404(db, appointment_id)
    before = _snapshot(appt, ("status",))
    _set_status(appt, S.cancelled)
    audit(db, user_id, "cancel", "appointment", appt.id, before, _snapshot(appt, before))
    _commit(db)
    db.refresh(appt)
    return appt
