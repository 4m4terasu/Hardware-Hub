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