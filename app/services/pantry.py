import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import PantryItem
from app.schemas.pantry import PantryItemCreate, PantryItemUpdate


def _normalise(name: str) -> str:
    """
    Canonical form used as the shelf-life cache key.
    'Chicken Breast', ' chicken  breast ', 'CHICKEN BREAST' → 'chicken breast'
    """
    return " ".join(name.lower().split())


async def get_items(db: AsyncSession, user_id: uuid.UUID) -> list[PantryItem]:
    """Return all non-deleted items for this user, newest first."""
    result = await db.execute(
        select(PantryItem)
        .where(PantryItem.user_id == user_id)
        .where(PantryItem.deleted_at.is_(None))   # soft delete filter
        .order_by(PantryItem.added_at.desc())
    )
    return list(result.scalars().all())


async def get_item(
    db: AsyncSession, item_id: uuid.UUID, user_id: uuid.UUID
) -> PantryItem | None:
    """
    Fetch a single item — enforces ownership by filtering on both
    item_id AND user_id. A user can never access another user's items
    even if they guess the UUID.
    """
    result = await db.execute(
        select(PantryItem)
        .where(PantryItem.id == item_id)
        .where(PantryItem.user_id == user_id)
        .where(PantryItem.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def create_item(
    db: AsyncSession, user_id: uuid.UUID, payload: PantryItemCreate
) -> PantryItem:
    item = PantryItem(
        user_id=user_id,
        name=payload.name.strip(),
        name_normalised=_normalise(payload.name),
        quantity=payload.quantity,
        unit=payload.unit,
        expiry_date=payload.expiry_date,
        # inferred_expiry will be set by the LLM service in Step 7
        # when expiry_date is None
        inferred_expiry=None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_item(
    db: AsyncSession, item: PantryItem, payload: PantryItemUpdate
) -> PantryItem:
    # Only update fields the client actually sent
    # model_dump(exclude_unset=True) is the key — it skips fields
    # the client didn't include, so we don't overwrite with None
    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(item, field, value)

    # If name changed, re-normalise so the cache key stays correct
    if "name" in updates:
        item.name_normalised = _normalise(updates["name"])

    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: PantryItem) -> None:
    """Soft delete — sets deleted_at instead of removing the row."""
    item.deleted_at = datetime.now(timezone.utc)
    await db.commit()


async def get_expiring_soon(
    db: AsyncSession, user_id: uuid.UUID, days: int = 3
) -> list[PantryItem]:
    """
    Returns items expiring within `days` days.
    Checks both expiry_date and inferred_expiry using COALESCE logic in Python.
    In Step 10 the Celery task will call this same service function.
    """
    from datetime import date, timedelta
    today = date.today()
    cutoff = today + timedelta(days=days)

    result = await db.execute(
        select(PantryItem)
        .where(PantryItem.user_id == user_id)
        .where(PantryItem.deleted_at.is_(None))
    )
    items = list(result.scalars().all())

    # Filter in Python rather than SQL so we can check both expiry columns
    return [
        item for item in items
        if (effective := item.expiry_date or item.inferred_expiry)
        and today <= effective <= cutoff
    ]
