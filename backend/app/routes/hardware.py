from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.models.hardware import Hardware
from backend.app.models.user import User
from backend.app.schemas.hardware import HardwareListItem

router = APIRouter(
    prefix="/api/hardware",
    tags=["hardware"],
    dependencies=[Depends(get_current_user)],
)

SortBy = Literal["id", "name", "brand", "purchase_date_raw", "status_raw"]
SortDir = Literal["asc", "desc"]

VALID_HARDWARE_STATUSES = {"Available", "In Use", "Repair"}
BLOCKING_NOTE_PHRASES = (
    "do not issue",
    "without service",
    "battery swelling",
)


def get_hardware_or_404(hardware_id: int, db: Session) -> Hardware:
    hardware = db.get(Hardware, hardware_id)

    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware item was not found.",
        )

    return hardware


def get_valid_status_or_400(hardware: Hardware) -> str:
    current_status = (hardware.status_raw or "").strip()

    if current_status not in VALID_HARDWARE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f'Hardware item has invalid status "{hardware.status_raw}" '
                "and cannot be processed."
            ),
        )

    return current_status


def has_blocking_rental_note(notes: str | None) -> bool:
    if not notes:
        return False

    normalized_notes = notes.casefold()
    return any(phrase in normalized_notes for phrase in BLOCKING_NOTE_PHRASES)


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


@router.post("/{hardware_id}/rent", response_model=HardwareListItem)
def rent_hardware(
    hardware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Hardware:
    hardware = get_hardware_or_404(hardware_id, db)
    current_status = get_valid_status_or_400(hardware)

    if has_blocking_rental_note(hardware.notes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This item cannot be rented: {hardware.notes}",
        )

    if current_status == "In Use":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is already in use and cannot be rented.",
        )

    if current_status == "Repair":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is under repair and cannot be rented.",
        )

    hardware.status_raw = "In Use"
    hardware.assigned_to = current_user.email

    db.commit()
    db.refresh(hardware)

    return hardware


@router.post("/{hardware_id}/return", response_model=HardwareListItem)
def return_hardware(
    hardware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Hardware:
    hardware = get_hardware_or_404(hardware_id, db)
    current_status = get_valid_status_or_400(hardware)

    if current_status == "Available":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is already available and cannot be returned.",
        )

    if current_status == "Repair":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is under repair and cannot be returned.",
        )

    hardware.status_raw = "Available"
    hardware.assigned_to = None

    db.commit()
    db.refresh(hardware)

    return hardware