from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.dependencies.auth import get_current_admin_user
from backend.app.models.hardware import Hardware
from backend.app.models.user import User
from backend.app.schemas.auth import UserCreateRequest, UserRead
from backend.app.schemas.hardware import HardwareCreateRequest, HardwareListItem
from backend.app.utils.security import get_password_hash

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_hardware_or_404(hardware_id: int, db: Session) -> Hardware:
    hardware = db.get(Hardware, hardware_id)

    if not hardware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hardware item was not found.",
        )

    return hardware


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        is_admin=payload.is_admin,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/hardware",
    response_model=HardwareListItem,
    status_code=status.HTTP_201_CREATED,
)
def create_hardware(
    payload: HardwareCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> Hardware:
    hardware = Hardware(
        name=payload.name,
        brand=payload.brand,
        purchase_date_raw=payload.purchase_date_raw,
        status_raw="Available",
        notes=payload.notes,
        assigned_to=None,
        history_text=payload.history_text,
    )

    db.add(hardware)
    db.commit()
    db.refresh(hardware)

    return hardware


@router.delete("/hardware/{hardware_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hardware(
    hardware_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> Response:
    hardware = get_hardware_or_404(hardware_id, db)
    current_status = (hardware.status_raw or "").strip()

    if current_status == "In Use":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is currently in use and cannot be deleted.",
        )

    db.delete(hardware)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/hardware/{hardware_id}/toggle-repair",
    response_model=HardwareListItem,
)
def toggle_repair_status(
    hardware_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
) -> Hardware:
    hardware = get_hardware_or_404(hardware_id, db)
    current_status = (hardware.status_raw or "").strip()

    if current_status == "Available":
        hardware.status_raw = "Repair"
        hardware.assigned_to = None
    elif current_status == "Repair":
        hardware.status_raw = "Available"
    elif current_status == "In Use":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is currently in use and cannot be moved to repair.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f'Hardware item has invalid status "{hardware.status_raw}" '
                "and repair status cannot be toggled."
            ),
        )

    db.commit()
    db.refresh(hardware)

    return hardware