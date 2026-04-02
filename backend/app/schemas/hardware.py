from pydantic import BaseModel, ConfigDict


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