"""Fill the database with synthetic (fake) dentists, working hours, patients and staff logins.

Usage:  python seed.py [number_of_patients]   (default 50; skips if patients already exist)

Dev logins (password = SEED_PASSWORD, default dentalflow-dev): admin@example.com,
reception@example.com, and dentist1..3@example.com (linked to the three dentists).
Never run this against production; create the real admin with create_admin.py.
"""

import os
import sys
from datetime import time

from faker import Faker
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Availability, Dentist, Patient, Role, User
from app.security import hash_password

DENTISTS = [
    ("Dr. Aye Chan", "General dentistry"),
    ("Dr. Min Thu", "Orthodontics"),
    ("Dr. Su Su", "Endodontics"),
]
# Mon-Fri 09-12 + 13-17 (lunch break 12-13), Sat 09-13.
WEEKLY_HOURS = [(d, time(9), time(12)) for d in range(5)] + [
    (d, time(13), time(17)) for d in range(5)
] + [(5, time(9), time(13))]


def seed(n_patients: int = 50) -> None:
    fake = Faker()
    Faker.seed(42)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Patient)):
            print("Database already has patients - skipping seed.")
            return

        pw = hash_password(os.getenv("SEED_PASSWORD", "dentalflow-dev"))
        db.add_all([
            User(email="admin@example.com", full_name="Clinic Admin", role=Role.admin, password_hash=pw),
            User(email="reception@example.com", full_name="Front Desk", role=Role.receptionist, password_hash=pw),
        ])
        for i, (name, specialty) in enumerate(DENTISTS, 1):
            login = User(email=f"dentist{i}@example.com", full_name=name, role=Role.dentist, password_hash=pw)
            db.add(login)
            db.flush()
            dentist = Dentist(
                user_id=login.id,
                full_name=name,
                specialty=specialty,
                phone=fake.numerify("09-###-###-###"),
                email=fake.unique.email(),
            )
            dentist_slots = [Availability(day_of_week=d, start_time=s, end_time=e) for d, s, e in WEEKLY_HOURS]
            db.add(dentist)
            db.flush()
            for slot in dentist_slots:
                slot.dentist_id = dentist.id
            db.add_all(dentist_slots)

        db.add_all(
            Patient(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                date_of_birth=fake.date_of_birth(minimum_age=3, maximum_age=90),
                gender=fake.random_element(["male", "female", "other"]),
                phone=fake.numerify("09-###-###-###"),
                email=fake.unique.email(),
                address=fake.address().replace("\n", ", "),
                medical_notes=fake.random_element([None, None, "Penicillin allergy", "Diabetic", "Pregnant"]),
            )
            for _ in range(n_patients)
        )
        db.commit()
        print(f"Seeded {len(DENTISTS)} dentists, {n_patients} patients and {len(DENTISTS) + 2} staff logins.")


if __name__ == "__main__":
    seed(int(sys.argv[1]) if len(sys.argv) > 1 else 50)
