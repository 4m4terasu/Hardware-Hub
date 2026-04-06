from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base, get_db
from backend.app.models.hardware import Hardware
from backend.app.models.user import User
from backend.app.routes.admin import router as admin_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.hardware import router as hardware_router
from backend.app.utils.security import get_password_hash


def seed_test_data(db: Session) -> None:
    admin_user = User(
        email="admin@booksy.com",
        hashed_password=get_password_hash("Admin123!"),
        is_admin=True,
    )
    regular_user = User(
        email="user1@booksy.com",
        hashed_password=get_password_hash("User123!"),
        is_admin=False,
    )

    hardware_items = [
        Hardware(
            id=1,
            name="Apple iPhone 13 Pro Max",
            brand="Apple",
            purchase_date_raw="2021-11-23",
            status_raw="Available",
            notes=None,
            assigned_to=None,
            history_text=None,
        ),
        Hardware(
            id=4,
            name="SAMSUNG Galaxy S21",
            brand="Samsung",
            purchase_date_raw="2021-11-23",
            status_raw="Available",
            notes=None,
            assigned_to=None,
            history_text=None,
        ),
        Hardware(
            id=5,
            name="Dell XPS 15 9510",
            brand="Dell",
            purchase_date_raw="2022-03-15",
            status_raw="Available",
            notes="Battery swelling, do not issue without service.",
            assigned_to=None,
            history_text=None,
        ),
        Hardware(
            id=6,
            name="Logitech MX Master 3",
            brand="Logitech",
            purchase_date_raw="2027-10-10",
            status_raw="Available",
            notes=None,
            assigned_to=None,
            history_text=None,
        ),
        Hardware(
            id=7,
            name="Sony WH-1000XM4",
            brand="Sony",
            purchase_date_raw="2022-01-12",
            status_raw="In Use",
            notes=None,
            assigned_to="j.doe@booksy.com",
            history_text=None,
        ),
        Hardware(
            id=9,
            name="iPad Pro 12.9",
            brand="Appel",
            purchase_date_raw="22-05-2023",
            status_raw="Available",
            notes=None,
            assigned_to=None,
            history_text=None,
        ),
        Hardware(
            id=10,
            name="Unknown Device",
            brand="",
            purchase_date_raw=None,
            status_raw="Unknown",
            notes=None,
            assigned_to=None,
            history_text=None,
        ),
        Hardware(
            id=11,
            name="MacBook Air M2",
            brand="Apple",
            purchase_date_raw="2023-08-01",
            status_raw="Available",
            notes=None,
            assigned_to=None,
            history_text="Returned by user with liquid damage. Keyboard sticky.",
        ),
    ]

    db.add_all([admin_user, regular_user, *hardware_items])
    db.commit()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    seed_db = testing_session_local()
    try:
        seed_test_data(seed_db)
    finally:
        seed_db.close()

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(hardware_router)
    app.include_router(admin_router)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def get_auth_headers(
    client: TestClient,
    email: str,
    password: str,
) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_cannot_rent_safety_flagged_hardware(client: TestClient) -> None:
    user_headers = get_auth_headers(client, "user1@booksy.com", "User123!")

    response = client.post("/api/hardware/5/rent", headers=user_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "This item cannot be rented: Battery swelling, do not issue without service."
    )


def test_non_admin_cannot_access_admin_endpoint(client: TestClient) -> None:
    user_headers = get_auth_headers(client, "user1@booksy.com", "User123!")

    response = client.post(
        "/api/admin/hardware",
        headers=user_headers,
        json={
            "name": "Unauthorized Test Device",
            "brand": "Apple",
            "purchase_date_raw": "2024-10-10",
            "notes": "Should fail",
            "history_text": "Permission test",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required."


def test_admin_cannot_delete_in_use_hardware(client: TestClient) -> None:
    admin_headers = get_auth_headers(client, "admin@booksy.com", "Admin123!")

    response = client.delete("/api/admin/hardware/7", headers=admin_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "This item is currently in use and cannot be deleted."
    )


def test_inventory_audit_detects_known_seed_traps(client: TestClient) -> None:
    admin_headers = get_auth_headers(client, "admin@booksy.com", "Admin123!")

    response = client.get("/api/hardware/audit", headers=admin_headers)

    assert response.status_code == 200

    payload = response.json()
    issue_codes = {finding["issue_code"] for finding in payload["findings"]}

    expected_issue_codes = {
        "SAFETY_NOTE_BLOCK",
        "FUTURE_PURCHASE_DATE",
        "INVALID_STATUS",
        "DUPLICATE_SEED_ID_SKIPPED",
        "MALFORMED_PURCHASE_DATE",
        "MISSING_BRAND",
        "MISSING_PURCHASE_DATE",
        "DAMAGE_HISTORY",
        "SUSPICIOUS_BRAND",
    }

    assert expected_issue_codes.issubset(issue_codes)
    assert payload["summary"]["high_severity_count"] >= 3
    assert payload["summary"]["total_findings"] >= len(expected_issue_codes)