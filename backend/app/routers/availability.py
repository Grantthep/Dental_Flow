from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.booking import free_slots
from app.db import get_db
from app.deps import current_user, require_roles
from app.models import Availability, Dentist, Role, TimeOff
from app.schemas import AvailabilityBlock, Slot, TimeOffCreate, TimeOffOut

router = APIRouter(tags=["availability"], dependencies=[Depends(current_user)])
admin = [Depends(require_roles(Role.admin))]


def _dentist_or_404(db: Session, dentist_id: int) -> Dentist:
    dentist = db.get(Dentist, dentist_id)
    if not dentist:
        raise HTTPException(404, "Dentist not found")
    return dentist


def _schedule(db: Session, dentist_id: int):
    return db.scalars(
        select(Availability)
        .where(Availability.dentist_id == dentist_id)
        .order_by(Availability.day_of_week, Availability.start_time)
    ).all()


@router.get("/dentists/{dentist_id}/availability", response_model=list[AvailabilityBlock])
def get_availability(dentist_id: int, db: Session = Depends(get_db)):
    _dentist_or_404(db, dentist_id)
    return _schedule(db, dentist_id)


@router.put("/dentists/{dentist_id}/availability", response_model=list[AvailabilityBlock], dependencies=admin)
def replace_availability(dentist_id: int, blocks: list[AvailabilityBlock], db: Session = Depends(get_db)):
    """Replace the whole weekly schedule. Breaks = gaps between blocks on the same day."""
    _dentist_or_404(db, dentist_id)
    ordered = sorted(blocks, key=lambda b: (b.day_of_week, b.start_time))
    for a, b in zip(ordered, ordered[1:]):
        if a.day_of_week == b.day_of_week and b.start_time < a.end_time:
            raise HTTPException(422, f"Blocks overlap on day {a.day_of_week}")
    db.execute(delete(Availability).where(Availability.dentist_id == dentist_id))
    db.add_all(Availability(dentist_id=dentist_id, **b.model_dump()) for b in ordered)
    db.commit()
    return _schedule(db, dentist_id)


@router.get("/dentists/{dentist_id}/time-off", response_model=list[TimeOffOut])
def list_time_off(dentist_id: int, db: Session = Depends(get_db)):
    _dentist_or_404(db, dentist_id)
    return db.scalars(select(TimeOff).where(TimeOff.dentist_id == dentist_id).order_by(TimeOff.start_at)).all()


@router.post("/dentists/{dentist_id}/time-off", response_model=TimeOffOut, status_code=201, dependencies=admin)
def add_time_off(dentist_id: int, body: TimeOffCreate, db: Session = Depends(get_db)):
    # Existing appointments in this period are left as they are; staff reschedule them by hand.
    _dentist_or_404(db, dentist_id)
    time_off = TimeOff(dentist_id=dentist_id, **body.model_dump())
    db.add(time_off)
    db.commit()
    db.refresh(time_off)
    return time_off


@router.delete("/time-off/{time_off_id}", status_code=204, dependencies=admin)
def delete_time_off(time_off_id: int, db: Session = Depends(get_db)):
    time_off = db.get(TimeOff, time_off_id)
    if not time_off:
        raise HTTPException(404, "Time off not found")
    db.delete(time_off)
    db.commit()


@router.get("/dentists/{dentist_id}/slots", response_model=list[Slot])
def get_slots(
    dentist_id: int,
    date: date,
    duration: int = Query(30, ge=15, le=240, description="minutes"),
    db: Session = Depends(get_db),
):
    _dentist_or_404(db, dentist_id)
    return [Slot(start_at=s, end_at=e) for s, e in free_slots(db, dentist_id, date, timedelta(minutes=duration))]
