from datetime import date, datetime

from openpyxl import Workbook
from sqlalchemy import select

from app.models import Patient
from import_patients import run

CSV = """﻿Patient Name,Mobile,DOB,Sex,E-mail,Allergies
Mya Win,09-111-222,25/12/1990,female,mya@example.com,Penicillin
Aung Ko Ko,09-333-444,1985-01-31,male,,
,09-555,01/01/2000,,,
Bad Phone,abc,,,,
Bad Date,09-777-888,31/02/2000,,,
Mya Win,09-111-222,,,,
"""


def test_csv_dry_run_then_commit(tmp_path, db):
    f = tmp_path / "patients.csv"
    f.write_text(CSV, encoding="utf-8")
    errors = tmp_path / "bad.csv"

    assert run(f, commit=False, date_format="%d/%m/%Y", errors_path=errors) == {"valid": 2, "skipped": 4}
    assert db.scalar(select(Patient).limit(1)) is None  # dry run wrote nothing
    assert len(errors.read_text(encoding="utf-8").splitlines()) == 5  # header + 4 bad rows

    assert run(f, commit=True, date_format="%d/%m/%Y", errors_path=None)["valid"] == 2
    mya = db.scalar(select(Patient).where(Patient.first_name == "Mya"))
    assert (mya.last_name, mya.date_of_birth, mya.medical_notes) == ("Win", date(1990, 12, 25), "Penicillin")
    assert db.scalar(select(Patient).where(Patient.first_name == "Aung Ko")).last_name == "Ko"

    # importing again finds them all as duplicates
    assert run(f, commit=True, date_format="%d/%m/%Y", errors_path=None)["valid"] == 0


def test_xlsx(tmp_path, db):
    wb = Workbook()
    wb.active.append(["First Name", "Surname", "Phone", "Birthday"])
    wb.active.append(["Su", "Su", "09-123-456", datetime(2001, 5, 6)])
    wb.active.append([None, None, None, None])  # blank row ignored
    f = tmp_path / "patients.xlsx"
    wb.save(f)

    assert run(f, commit=True, date_format="%d/%m/%Y", errors_path=None) == {"valid": 1, "skipped": 0}
    assert db.scalar(select(Patient)).date_of_birth == date(2001, 5, 6)
