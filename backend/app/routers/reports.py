"""Clinic analytics. Dates are clinic-local days; date_from and date_to are both inclusive."""

from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.booking import CLINIC_TZ
from app.db import get_db

router = APIRouter(prefix="/reports", tags=["reports"])

MAX_DAYS = 3 * 366

# Shared status counts. no_show_rate only counts appointments that have happened (completed + no_show).
COUNTS = """
    count(a.id)                                         AS total,
    count(*) FILTER (WHERE a.status = 'completed')      AS completed,
    count(*) FILTER (WHERE a.status = 'cancelled')      AS cancelled,
    count(*) FILTER (WHERE a.status = 'no_show')        AS no_show,
    count(*) FILTER (WHERE a.status IN ('booked', 'confirmed')) AS upcoming
"""


class Counts(BaseModel):
    total: int
    completed: int
    cancelled: int
    no_show: int
    upcoming: int


class PeriodRow(Counts):
    period: date


class DentistRow(Counts):
    dentist_id: int
    full_name: str
    booked_minutes: int


class Rates(Counts):
    cancellation_rate: float | None
    no_show_rate: float | None


def _range(date_from: date, date_to: date) -> dict:
    if date_to < date_from:
        raise HTTPException(422, "date_to must be on or after date_from")
    if (date_to - date_from).days > MAX_DAYS:
        raise HTTPException(422, f"Range too long (max {MAX_DAYS} days)")
    return {
        "start": datetime.combine(date_from, time(), CLINIC_TZ),
        "end": datetime.combine(date_to + timedelta(days=1), time(), CLINIC_TZ),
        "tz": CLINIC_TZ.key,
    }


@router.get("/appointments", response_model=list[PeriodRow])
def appointments_over_time(
    date_from: date,
    date_to: date,
    group_by: Literal["day", "week", "month"] = "day",
    dentist_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Counts per day / week (Mon start) / month, including periods with zero appointments."""
    p = _range(date_from, date_to) | {"unit": group_by, "d_from": date_from, "d_to": date_to, "dentist_id": dentist_id}
    rows = db.execute(text(f"""
        WITH periods AS (
            SELECT generate_series(date_trunc(:unit, CAST(:d_from AS timestamp)), CAST(:d_to AS timestamp),
                                   CAST('1 ' || :unit AS interval)) AS period
        ), a AS (
            SELECT id, status, date_trunc(:unit, start_at AT TIME ZONE :tz) AS period
            FROM appointments
            WHERE start_at >= :start AND start_at < :end
              AND (CAST(:dentist_id AS int) IS NULL OR dentist_id = :dentist_id)
        )
        SELECT CAST(p.period AS date) AS period, {COUNTS}
        FROM periods p LEFT JOIN a ON a.period = p.period
        GROUP BY p.period ORDER BY p.period
    """), p).mappings()
    return [PeriodRow(**r) for r in rows]


@router.get("/dentists", response_model=list[DentistRow])
def per_dentist(date_from: date, date_to: date, db: Session = Depends(get_db)):
    """Totals per dentist; booked_minutes = chair time of non-cancelled, non-no-show appointments."""
    rows = db.execute(text(f"""
        SELECT d.id AS dentist_id, d.full_name, {COUNTS},
               COALESCE(CAST(SUM(EXTRACT(EPOCH FROM a.end_at - a.start_at) / 60)
                    FILTER (WHERE a.status NOT IN ('cancelled', 'no_show')) AS int), 0) AS booked_minutes
        FROM dentists d
        LEFT JOIN appointments a ON a.dentist_id = d.id AND a.start_at >= :start AND a.start_at < :end
        GROUP BY d.id
        HAVING d.is_active OR count(a.id) > 0
        ORDER BY d.full_name
    """), _range(date_from, date_to)).mappings()
    return [DentistRow(**r) for r in rows]


@router.get("/rates", response_model=Rates)
def rates(date_from: date, date_to: date, dentist_id: int | None = None, db: Session = Depends(get_db)):
    """cancellation_rate = cancelled / total; no_show_rate = no_show / (completed + no_show). null if no data."""
    r = db.execute(text(f"""
        SELECT {COUNTS} FROM appointments a
        WHERE a.start_at >= :start AND a.start_at < :end
          AND (CAST(:dentist_id AS int) IS NULL OR a.dentist_id = :dentist_id)
    """), _range(date_from, date_to) | {"dentist_id": dentist_id}).mappings().one()
    attended = r["completed"] + r["no_show"]
    return Rates(
        **r,
        cancellation_rate=round(r["cancelled"] / r["total"], 4) if r["total"] else None,
        no_show_rate=round(r["no_show"] / attended, 4) if attended else None,
    )
