from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.booking import BookingError
from app.routers import appointments, audit_logs, availability, dentists, patients, reports

app = FastAPI(title="DentalFlow API", version="0.1.0")

for r in (patients, dentists, availability, appointments, audit_logs, reports):
    app.include_router(r.router, prefix="/api/v1")


@app.exception_handler(BookingError)
def booking_error(_: Request, exc: BookingError):
    return JSONResponse({"detail": exc.detail, "code": exc.code}, status_code=exc.status_code)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
