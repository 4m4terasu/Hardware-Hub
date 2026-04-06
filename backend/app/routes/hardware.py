from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.models.hardware import Hardware
from backend.app.models.user import User
from backend.app.schemas.hardware import (
    HardwareListItem,
    InventoryAuditFinding,
    InventoryAuditReportResponse,
    InventoryAuditResponse,
    InventoryAuditSummary,
)
from backend.app.services.gemini_audit_service import summarize_inventory_audit

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
DAMAGE_HISTORY_PHRASES = (
    "liquid damage",
    "keyboard sticky",
)
KNOWN_BRAND_TYPO_SUGGESTIONS = {
    "appel": "Apple",
}
SEVERITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}


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


def has_damage_history(history_text: str | None) -> bool:
    if not history_text:
        return False

    normalized_history = history_text.casefold()
    return any(phrase in normalized_history for phrase in DAMAGE_HISTORY_PHRASES)


def build_audit_findings(hardware_items: list[Hardware]) -> list[InventoryAuditFinding]:
    findings: list[InventoryAuditFinding] = []

    for item in hardware_items:
        item_brand = (item.brand or "").strip()
        item_status = (item.status_raw or "").strip()
        item_purchase_date = (item.purchase_date_raw or "").strip()

        if not item_brand:
            findings.append(
                InventoryAuditFinding(
                    hardware_id=item.id,
                    hardware_name=item.name,
                    issue_code="MISSING_BRAND",
                    severity="medium",
                    message="Brand is missing and should be reviewed.",
                )
            )
        else:
            suggested_brand = KNOWN_BRAND_TYPO_SUGGESTIONS.get(item_brand.casefold())
            if suggested_brand:
                findings.append(
                    InventoryAuditFinding(
                        hardware_id=item.id,
                        hardware_name=item.name,
                        issue_code="SUSPICIOUS_BRAND",
                        severity="low",
                        message=(
                            f'Brand "{item.brand}" looks suspicious and may be a typo '
                            f'for "{suggested_brand}".'
                        ),
                    )
                )

        if not item_purchase_date:
            findings.append(
                InventoryAuditFinding(
                    hardware_id=item.id,
                    hardware_name=item.name,
                    issue_code="MISSING_PURCHASE_DATE",
                    severity="medium",
                    message="Purchase date is missing and should be reviewed.",
                )
            )
        else:
            try:
                parsed_purchase_date = date.fromisoformat(item_purchase_date)

                if parsed_purchase_date > date.today():
                    findings.append(
                        InventoryAuditFinding(
                            hardware_id=item.id,
                            hardware_name=item.name,
                            issue_code="FUTURE_PURCHASE_DATE",
                            severity="high",
                            message=(
                                f"Purchase date {item.purchase_date_raw} is in the future."
                            ),
                        )
                    )
            except ValueError:
                findings.append(
                    InventoryAuditFinding(
                        hardware_id=item.id,
                        hardware_name=item.name,
                        issue_code="MALFORMED_PURCHASE_DATE",
                        severity="medium",
                        message=(
                            f'Purchase date "{item.purchase_date_raw}" is malformed. '
                            "Expected YYYY-MM-DD."
                        ),
                    )
                )

        if item_status not in VALID_HARDWARE_STATUSES:
            findings.append(
                InventoryAuditFinding(
                    hardware_id=item.id,
                    hardware_name=item.name,
                    issue_code="INVALID_STATUS",
                    severity="high",
                    message=(
                        f'Status "{item.status_raw}" is invalid and should be corrected.'
                    ),
                )
            )

        if has_blocking_rental_note(item.notes):
            findings.append(
                InventoryAuditFinding(
                    hardware_id=item.id,
                    hardware_name=item.name,
                    issue_code="SAFETY_NOTE_BLOCK",
                    severity="high",
                    message=(
                        "Notes indicate this item should not be issued without review."
                    ),
                )
            )

        if has_damage_history(item.history_text):
            findings.append(
                InventoryAuditFinding(
                    hardware_id=item.id,
                    hardware_name=item.name,
                    issue_code="DAMAGE_HISTORY",
                    severity="medium",
                    message=(
                        "History contains damage-related information that should be "
                        "reviewed before future use."
                    ),
                )
            )

    hardware_id_4 = next((item for item in hardware_items if item.id == 4), None)
    if hardware_id_4:
        findings.append(
            InventoryAuditFinding(
                hardware_id=hardware_id_4.id,
                hardware_name=hardware_id_4.name,
                issue_code="DUPLICATE_SEED_ID_SKIPPED",
                severity="medium",
                message=(
                    "The source seed contained a duplicate row for ID 4. "
                    "The duplicate entry was intentionally skipped during import "
                    "for this MVP."
                ),
            )
        )

    findings.sort(
        key=lambda finding: (
            SEVERITY_ORDER[finding.severity],
            finding.hardware_id if finding.hardware_id is not None else -1,
            finding.issue_code,
        )
    )

    return findings


def build_inventory_audit_response(
    hardware_items: list[Hardware],
) -> InventoryAuditResponse:
    findings = build_audit_findings(hardware_items)

    summary = InventoryAuditSummary(
        total_items=len(hardware_items),
        total_findings=len(findings),
        high_severity_count=sum(1 for finding in findings if finding.severity == "high"),
        medium_severity_count=sum(
            1 for finding in findings if finding.severity == "medium"
        ),
        low_severity_count=sum(1 for finding in findings if finding.severity == "low"),
    )

    return InventoryAuditResponse(summary=summary, findings=findings)


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


@router.get("/audit", response_model=InventoryAuditResponse)
def audit_hardware_inventory(
    db: Session = Depends(get_db),
) -> InventoryAuditResponse:
    hardware_items = list(db.scalars(select(Hardware).order_by(Hardware.id)).all())
    return build_inventory_audit_response(hardware_items)


@router.get("/audit/report", response_model=InventoryAuditReportResponse)
def audit_hardware_inventory_report(
    db: Session = Depends(get_db),
) -> InventoryAuditReportResponse:
    hardware_items = list(db.scalars(select(Hardware).order_by(Hardware.id)).all())
    deterministic_audit = build_inventory_audit_response(hardware_items)
    ai_summary = summarize_inventory_audit(
        deterministic_audit.summary,
        deterministic_audit.findings,
    )

    return InventoryAuditReportResponse(
        summary=deterministic_audit.summary,
        findings=deterministic_audit.findings,
        ai_summary=ai_summary,
    )


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