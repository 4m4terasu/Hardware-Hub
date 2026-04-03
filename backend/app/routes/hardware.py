from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models.hardware import Hardware
from backend.app.schemas.hardware import HardwareListItem

router = APIRouter(prefix="/api/hardware", tags=["hardware"])

SortBy = Literal["id", "name", "brand", "purchase_date_raw", "status_raw"]
SortDir = Literal["asc", "desc"]


@router.get("", response_model=list[HardwareListItem])
def list_hardware(
    status: str | None = Query(default=None),
    brand: str | None = Query(default=None),
    sort_by: SortBy = Query(default="id"),
    sort_dir: SortDir = Query(default="asc"),
    db: Session = Depends(get_db),
) -> list[Hardware]:
    statement = select(Hardware)

    if status:
        statement = statement.where(Hardware.status_raw == status)

    if brand:
        statement = statement.where(Hardware.brand == brand)

    sort_column = getattr(Hardware, sort_by)
    order_by_clause = asc(sort_column) if sort_dir == "asc" else desc(sort_column)
    statement = statement.order_by(order_by_clause)

    hardware_items = db.scalars(statement).all()
    return list(hardware_items)