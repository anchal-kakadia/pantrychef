import uuid
from datetime import date, datetime

from pydantic import BaseModel, field_validator


class PantryItemCreate(BaseModel):
    """What the client sends when adding an item."""
    name: str
    quantity: float | None = None
    unit: str | None = None
    expiry_date: date | None = None  # NULL triggers LLM inference in Step 7

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Item name cannot be empty")
        return v


class PantryItemUpdate(BaseModel):
    """All fields optional — client sends only what changed (PATCH semantics)."""
    name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    expiry_date: date | None = None


class PantryItemResponse(BaseModel):
    """What we send back. Exposes both expiry fields so UI can show either."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    name_normalised: str
    quantity: float | None
    unit: str | None
    expiry_date: date | None
    inferred_expiry: date | None
    added_at: datetime
    deleted_at: datetime | None

    # effective_expiry is a computed convenience field — the UI uses
    # whichever expiry is set, without having to pick between the two
    @property
    def effective_expiry(self) -> date | None:
        return self.expiry_date or self.inferred_expiry

    model_config = {"from_attributes": True}
    