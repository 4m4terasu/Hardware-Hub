from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.dependencies.auth import get_current_admin_user
from backend.app.models.user import User
from backend.app.schemas.auth import UserCreateRequest, UserRead
from backend.app.utils.security import get_password_hash

router = APIRouter(prefix="/api/admin", tags=["admin"])


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