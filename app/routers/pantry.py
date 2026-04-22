import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User
from app.routers.users import get_current_user
from app.schemas.pantry import PantryItemCreate, PantryItemResponse, PantryItemUpdate
from app.services import pantry as pantry_service
from app.services.pantry import _normalise
from app.services.shelf_life import compute_inferred_expiry, get_shelf_life_days

router = APIRouter(prefix="/pantry", tags=["pantry"])


async def _get_item_or_404(
    item_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ...:
    """
    Shared helper — fetch item and raise 404 if not found or not owned.
    Used by GET single, PATCH, and DELETE to avoid repeating the same logic.
    """
    from app.models.models import PantryItem
    item = await pantry_service.get_item(db, item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.get("/items", response_model=list[PantryItemResponse])
async def list_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await pantry_service.get_items(db, current_user.id)


@router.post("/items", response_model=PantryItemResponse, status_code=201)
async def add_item(
    payload: PantryItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Create the item first
    item = await pantry_service.create_item(db, current_user.id, payload)

    # If user didn't provide expiry, infer it via LLM + cache
    if payload.expiry_date is None:
        days = await get_shelf_life_days(db, item.name_normalised)
        item.inferred_expiry = compute_inferred_expiry(item.added_at.date(), days)
        await db.commit()
        await db.refresh(item)

    return item


@router.get("/items/expiring-soon", response_model=list[PantryItemResponse])
async def expiring_soon(
    days: int = Query(default=3, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Must be defined BEFORE /items/{item_id} — FastAPI matches routes
    top to bottom, and 'expiring-soon' would be treated as an item_id
    (a UUID) and fail validation if the specific route comes first.
    """
    return await pantry_service.get_expiring_soon(db, current_user.id, days)


@router.get("/items/{item_id}", response_model=PantryItemResponse)
async def get_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_item_or_404(item_id, current_user, db)


@router.patch("/items/{item_id}", response_model=PantryItemResponse)
async def update_item(
    item_id: uuid.UUID,
    payload: PantryItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(item_id, current_user, db)
    return await pantry_service.update_item(db, item, payload)


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """204 No Content — successful delete returns no body."""
    item = await _get_item_or_404(item_id, current_user, db)
    await pantry_service.delete_item(db, item)
    