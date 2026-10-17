from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Dentist
from app.schemas import DentistCreate, DentistOut, DentistUpdate

router = APIRouter(prefix="/dentists", tags=["dentists"])


def _get_or_404(db: Session, dentist_id: int) -> Dentist:
    dentist = db.get(Dentist, dentist_id)
    if not dentist:
        raise HTTPException(404, "Dentist not found")
    return dentist


def _commit(db: Session):
    # user_id is a FK + unique: bad or already-linked user -> 409, not 500.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "user_id does not exist or is already linked to another dentist")


@router.get("", response_model=list[DentistOut])
def list_dentists(include_inactive: bool = False, db: Session = Depends(get_db)):
    stmt = select(Dentist).order_by(Dentist.full_name)
    if not include_inactive:
        stmt = stmt.where(Dentist.is_active)
    return db.scalars(stmt).all()


@router.post("", response_model=DentistOut, status_code=201)
def create_dentist(body: DentistCreate, db: Session = Depends(get_db)):
    dentist = Dentist(**body.model_dump())
    db.add(dentist)
    _commit(db)
    db.refresh(dentist)
    return dentist


@router.get("/{dentist_id}", response_model=DentistOut)
def get_dentist(dentist_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, dentist_id)


@router.patch("/{dentist_id}", response_model=DentistOut)
def update_dentist(dentist_id: int, body: DentistUpdate, db: Session = Depends(get_db)):
    dentist = _get_or_404(db, dentist_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(dentist, field, value)
    _commit(db)
    db.refresh(dentist)
    return dentist
