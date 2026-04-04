from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.db import Base, engine

## So SQLAlchemy knows about both tables before create_all() runs.
from backend.app.models.hardware import Hardware  # noqa: F401
from backend.app.models.user import User  # noqa: F401

from backend.app.routes.hardware import router as hardware_router
from backend.app.services.seed_service import seed_hardware_if_empty
from backend.app.services.user_seed_service import seed_admin_if_missing


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_hardware_if_empty()
    seed_admin_if_missing()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


app.include_router(hardware_router)