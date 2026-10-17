import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.booking import BookingError
from app.routers import appointments, audit_logs, auth, availability, dentists, patients, reports, users

app = FastAPI(title="DentalFlow API", version="0.1.0")

# Comma-separated list of frontend origins, e.g. "https://dentalflow.example.com".
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

for r in (auth, users, patients, dentists, availability, appointments, audit_logs, reports):
    app.include_router(r.router, prefix="/api/v1")


@app.exception_handler(BookingError)
def booking_error(_: Request, exc: BookingError):
    return JSONResponse({"detail": exc.detail, "code": exc.code}, status_code=exc.status_code)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
