import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    DATE,
    JSON,
    TEXT,
    VARCHAR,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        VARCHAR(255),
        unique=True,
        nullable=False,
        index=True,          # we query by email on every login — index speeds this up
    )
    hashed_password: Mapped[str] = mapped_column(TEXT, nullable=False)

    # JSONB lets us store flexible structure without separate columns.
    # e.g. {"high_protein": true, "spice_level": 3, "allergens": ["nuts", "dairy"]}
    # We use JSON here for simplicity; Postgres treats it as JSONB automatically via SQLAlchemy
    dietary_prefs: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # DB sets this, not Python — more reliable
        nullable=False,
    )

    # Relationship — lets us do user.pantry_items in Python
    # cascade="all, delete-orphan" means deleting a user deletes their items too
    pantry_items: Mapped[list["PantryItem"]] = relationship(
        "PantryItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_logs: Mapped[list["NotificationLog"]] = relationship(
        "NotificationLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class PantryItem(Base):
    __tablename__ = "pantry_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,          # we filter pantry items by user_id on every request
    )
    name: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)

    # Normalised name is used as the cache key for shelf life lookups.
    # "Chicken Breast", "chicken breast", " Chicken  Breast " all → "chicken breast"
    name_normalised: Mapped[str] = mapped_column(VARCHAR(200), nullable=False, index=True)

    quantity: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    unit: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    # NULL means the user didn't provide an expiry — triggers LLM inference in Step 7
    expiry_date: Mapped[date | None] = mapped_column(DATE, nullable=True)

    # Computed from shelf_life_cache + added_at when expiry_date is NULL
    inferred_expiry: Mapped[date | None] = mapped_column(DATE, nullable=True)

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Soft delete — we set this instead of actually deleting the row.
    # This lets us show "undo" in the UI and keeps data for analytics later.
    # Queries filter WHERE deleted_at IS NULL to get "active" items.
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="pantry_items")


class ShelfLifeCache(Base):
    __tablename__ = "shelf_life_cache"

    # The normalised item name IS the primary key — it's the lookup key.
    # No UUID needed here; we're building a key-value cache table.
    item_name_key: Mapped[str] = mapped_column(VARCHAR(200), primary_key=True)

    shelf_life_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Track which model produced this result.
    # If we switch from gpt-3.5-turbo to gpt-4o later, we can
    # invalidate old entries and re-infer with the better model.
    source_model: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Store the list of item IDs that were included in this alert batch.
    # ARRAY of UUIDs — native Postgres array type.
    item_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        default=list,
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # SES returns a message ID on every send.
    # We store it so we can trace bounces and delivery failures later.
    ses_message_id: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="notification_logs")