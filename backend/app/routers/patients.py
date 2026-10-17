from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Patient
from app.schemas import Page, PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


def _get_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


@router.get("", response_model=Page[PatientOut])
def list_patients(
    q: str | None = Query(None, description="Search name or phone"),
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Patient)
    if not include_inactive:
        stmt = stmt.where(Patient.is_active)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                (Patient.first_name + " " + Patient.last_name).ilike(like),
                Patient.phone.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(Patient.last_name, Patient.first_name, Patient.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(body: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**body.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, patient_id)


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, body: PatientUpdate, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient
