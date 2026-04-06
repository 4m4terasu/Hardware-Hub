from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HardwareListItem(BaseModel):
    id: int
    name: str
    brand: str | None = None
    purchase_date_raw: str | None = None
    status_raw: str | None = None
    notes: str | None = None
    assigned_to: str | None = None
    history_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HardwareCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    brand: str | None = Field(default=None, max_length=255)
    purchase_date_raw: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    history_text: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class InventoryAuditFinding(BaseModel):
    hardware_id: int | None = None
    hardware_name: str | None = None
    issue_code: str
    severity: Literal["high", "medium", "low"]
    message: str


class InventoryAuditSummary(BaseModel):
    total_items: int
    total_findings: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int


class InventoryAuditResponse(BaseModel):
    summary: InventoryAuditSummary
    findings: list[InventoryAuditFinding]