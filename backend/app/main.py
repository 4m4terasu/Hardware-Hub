from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.db import Base, engine
from backend.app.services.seed_service import seed_hardware_if_empty
from backend.app.routes.hardware import router as hardware_router

app = FastAPI(title=settings.app_name)
app.include_router(hardware_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_hardware_if_empty()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hardware Hub backend is running"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }