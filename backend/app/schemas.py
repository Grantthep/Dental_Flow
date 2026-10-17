from datetime import date, datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

T = TypeVar("T")

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 ()-]{6,30}$")]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


# ---------- Patients ----------
class PatientCreate(BaseModel):
    first_name: Name
    last_name: Name
    phone: Phone
    date_of_birth: date | None = None
    gender: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=255)
    medical_notes: str | None = None


class PatientUpdate(BaseModel):
    first_name: Name | None = None
    last_name: Name | None = None
    phone: Phone | None = None
    date_of_birth: date | None = None
    gender: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    address: str | None = Field(None, max_length=255)
    medical_notes: str | None = None
    is_active: bool | None = None


class PatientOut(PatientCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None = None  # don't re-validate stored values on the way out
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------- Dentists ----------
class DentistCreate(BaseModel):
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
    specialty: str | None = Field(None, max_length=100)
    phone: Phone | None = None
    email: EmailStr | None = None
    user_id: int | None = None


class DentistUpdate(BaseModel):
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)] | None = None
    specialty: str | None = Field(None, max_length=100)
    phone: Phone | None = None
    email: EmailStr | None = None
    user_id: int | None = None
    is_active: bool | None = None


class DentistOut(DentistCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str | None = None
    is_active: bool
    created_at: datetime
