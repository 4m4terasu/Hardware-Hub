from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models.hardware import Hardware
from backend.app.schemas.hardware import HardwareListItem

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("", response_model=list[HardwareListItem])
def list_hardware(db: Session = Depends(get_db)) -> list[Hardware]:
    statement = select(Hardware).order_by(Hardware.id.asc())
    hardware_items = db.scalars(statement).all()
    return list(hardware_items)