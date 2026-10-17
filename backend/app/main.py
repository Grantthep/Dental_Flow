from fastapi import FastAPI

from app.routers import dentists, patients

app = FastAPI(title="DentalFlow API", version="0.1.0")

app.include_router(patients.router, prefix="/api/v1")
app.include_router(dentists.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
