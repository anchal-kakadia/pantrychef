import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserRegister(BaseModel):
    """What the client sends to register."""
    email: EmailStr          # Pydantic validates email format automatically
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v.encode()) > 72:
            raise ValueError("Password must be 72 characters or fewer")
        return v


class UserLogin(BaseModel):
    """What the client sends to log in."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """What we send back — never expose hashed_password."""
    id: uuid.UUID
    email: str
    dietary_prefs: dict
    created_at: datetime

    model_config = {"from_attributes": True}  # lets Pydantic read SQLAlchemy models


class TokenResponse(BaseModel):
    """JWT response after login or register."""
    access_token: str
    token_type: str = "bearer"


class DietaryPrefs(BaseModel):
    """Shape of the dietary_prefs JSONB field."""
    high_protein: bool = False
    spice_level: int = 3          # 1–5
    allergens: list[str] = []