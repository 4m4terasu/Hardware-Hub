from sqlalchemy import select

from backend.app.config import settings
from backend.app.db import SessionLocal
from backend.app.models.user import User
from backend.app.utils.security import get_password_hash


def seed_admin_if_missing() -> None:
    db = SessionLocal()

    try:
        existing_admin = db.scalar(
            select(User).where(User.is_admin.is_(True)).limit(1)
        )

        if existing_admin:
            print("Admin user already exists. Skipping admin seed.")
            return

        admin_user = User(
            email=settings.bootstrap_admin_email,
            hashed_password=get_password_hash(settings.bootstrap_admin_password),
            is_admin=True,
        )

        db.add(admin_user)
        db.commit()

        print(
            f"Created bootstrap admin user: {settings.bootstrap_admin_email}"
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()