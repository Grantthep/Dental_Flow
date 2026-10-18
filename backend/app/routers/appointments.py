from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import AwareDatetime
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import audit
from app.booking import BookingError, check_bookable
from app.db import get_db
from app.deps import STAFF, current_user, current_user_id, own_dentist_id, require_roles
from app.models import Appointment, AppointmentStatus as S, Role, Treatment, User
from app.schemas import (
    AppointmentCreate, AppointmentOut, AppointmentUpdate, Page, TimeRange, TreatmentCreate, TreatmentOut,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])
staff = [Depends(require_roles(*STAFF))]

# Allowed status changes; completed / cancelled / no_show are final.
TRANSITIONS = {
    S.booked: {S.confirmed, S.completed, S.cancelled, S.no_show},
    S.confirmed: {S.completed, S.cancelled, S.no_show},
}


def _snapshot(appt: Appointment, fields) -> dict:
    return {f: getattr(appt, f) for f in fields}


# Dentists may only change these on their own appointments (cancel / reschedule is front desk).
DENTIST_FIELDS = {"status", "notes"}
DENTIST_STATUSES = {S.completed, S.no_show}


def _get_or_404(db: Session, appointment_id: int, user: User | None = None) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    # A dentist sees other dentists' appointments as not found.
    if not appt or (user and user.role == Role.dentist and appt.dentist_id != own_dentist_id(db, user)):
        raise HTTPException(404, "Appointment not found")
    return appt


def _commit(db: Session, step=None):
    # Two requests can pass check_bookable at the same moment; the exclusion constraint catches the loser.
    # It fires on whichever write reaches the DB first: flush() on create, commit() otherwise.
    try:
        (step or db.commit)()
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
    date_from: AwareDatetime | None = Query(None, description="start_at >= this (with timezone)"),
    date_to: AwareDatetime | None = Query(None, description="start_at < this (with timezone)"),
    dentist_id: int | None = None,
    patient_id: int | None = None,
    status: list[S] | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if user.role == Role.dentist:
        own = own_dentist_id(db, user)
        if dentist_id and dentist_id != own:
            raise HTTPException(403, "Dentists can only view their own appointments")
        dentist_id = own
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


@router.post("", response_model=AppointmentOut, status_code=201, dependencies=staff)
def create_appointment(body: AppointmentCreate, db: Session = Depends(get_db), user_id=Depends(current_user_id)):
    check_bookable(db, body.dentist_id, body.patient_id, body.start_at, body.end_at)
    appt = Appointment(**body.model_dump(), created_by=user_id)
    db.add(appt)
    _commit(db, db.flush)
    audit(db, user_id, "create", "appointment", appt.id, after=_snapshot(appt, ("start_at", "end_at", "reason")))
    _commit(db)
    db.refresh(appt)
    return appt


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _get_or_404(db, appointment_id, user)


@router.patch("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int, body: AppointmentUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    user_id = user.id
    appt = _get_or_404(db, appointment_id, user)
    changes = body.model_dump(exclude_unset=True)
    if user.role == Role.dentist and changes.keys() - DENTIST_FIELDS:
        raise HTTPException(403, "Dentists can only change status and notes")
    if user.role == Role.dentist and changes.get("status", S.completed) not in DENTIST_STATUSES:
        raise HTTPException(403, "Dentists can only mark appointments completed or no-show")
    before = _snapshot(appt, changes)
    if "status" in changes:
        _set_status(appt, changes.pop("status"))
    for field, value in changes.items():
        setattr(appt, field, value)
    audit(db, user_id, "update", "appointment", appt.id, before, _snapshot(appt, before))
    _commit(db)
    db.refresh(appt)
    return appt


@router.post("/{appointment_id}/reschedule", response_model=AppointmentOut, dependencies=staff)
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


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut, dependencies=staff)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), user_id=Depends(current_user_id)):
    appt = _get_or_404(db, appointment_id)
    before = _snapshot(appt, ("status",))
    _set_status(appt, S.cancelled)
    audit(db, user_id, "cancel", "appointment", appt.id, before, _snapshot(appt, before))
    _commit(db)
    db.refresh(appt)
    return appt


@router.get("/{appointment_id}/treatments", response_model=list[TreatmentOut])
def list_treatments(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _get_or_404(db, appointment_id, user)
    return db.scalars(
        select(Treatment).where(Treatment.appointment_id == appointment_id).order_by(Treatment.id)
    ).all()


@router.post("/{appointment_id}/treatments", response_model=TreatmentOut, status_code=201,
             dependencies=[Depends(require_roles(Role.admin, Role.dentist))])
def add_treatment(
    appointment_id: int, body: TreatmentCreate, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    appt = _get_or_404(db, appointment_id, user)
    if appt.status in (S.cancelled, S.no_show):
        raise BookingError(409, "bad_status", f"Cannot add treatment to a {appt.status.value} appointment")
    if appt.start_at > datetime.now(UTC):
        raise BookingError(409, "too_early", "Cannot add treatment before the appointment starts")
    treatment = Treatment(appointment_id=appt.id, created_by=user.id, **body.model_dump())
    db.add(treatment)
    db.flush()
    audit(db, user.id, "create", "treatment", treatment.id, after=body.model_dump())
    db.commit()
    db.refresh(treatment)
    return treatment
