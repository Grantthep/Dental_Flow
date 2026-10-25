from datetime import date, datetime, time
from typing import Annotated, Generic, TypeVar

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, StringConstraints, model_validator

from app.models import AppointmentStatus, Role

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


# ---------- Availability ----------
class TimeRange(BaseModel):
    start_at: AwareDatetime
    end_at: AwareDatetime

    @model_validator(mode="after")
    def _order(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class TimeOffCreate(TimeRange):
    reason: str | None = Field(None, max_length=255)


class AvailabilityBlock(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day_of_week: int = Field(ge=0, le=6, description="0=Mon .. 6=Sun")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class TimeOffOut(TimeOffCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dentist_id: int


class Slot(BaseModel):
    start_at: datetime
    end_at: datetime


# ---------- Appointments ----------
class AppointmentCreate(TimeRange):
    patient_id: int
    dentist_id: int
    reason: str | None = Field(None, max_length=255)
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    status: AppointmentStatus | None = None
    reason: str | None = Field(None, max_length=255)
    notes: str | None = None


class PatientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    phone: str


class DentistBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    dentist_id: int
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    reason: str | None
    notes: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    patient: PatientBrief
    dentist: DentistBrief


# ---------- Audit ----------
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int
    changes: dict | None
    created_at: datetime


# ---------- Users / auth ----------
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
    role: Role
    password: Password


class UserUpdate(BaseModel):
    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)] | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: Password | None = None  # admin password reset


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserOut


class PasswordChange(BaseModel):
    current_password: str
    new_password: Password


# ---------- Treatments ----------
class TreatmentCreate(BaseModel):
    tooth: str | None = Field(None, pattern=r"^[1-8][1-8]$", description="FDI tooth number, e.g. 36; omit for whole mouth")
    procedure: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
    notes: str | None = None


class TreatmentAppointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_at: datetime
    dentist: DentistBrief


class TreatmentOut(TreatmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int | None
    created_at: datetime
    appointment: TreatmentAppointment
