import os
from datetime import datetime

from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/dentalflow"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    # All timestamps are timestamptz (stored UTC).
    type_annotation_map = {datetime: DateTime(timezone=True)}


def get_db():
    with SessionLocal() as db:
        yield db
