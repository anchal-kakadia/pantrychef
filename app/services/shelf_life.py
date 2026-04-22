from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ShelfLifeCache
from app.services.llm import infer_shelf_life_days

# The model name gets stored with the cache entry so we can
# invalidate old entries if we later upgrade to a better model.
_MODEL_TAG = "gpt-3.5-turbo"

# Safety fallback when LLM returns garbage — better to show
# something than crash the add-item flow.
_DEFAULT_FALLBACK_DAYS = 7


async def get_shelf_life_days(db: AsyncSession, name_normalised: str) -> int:
    """
    Returns shelf life in days for this item name.
    Cache-first: checks DB before calling LLM.
    On first call for a new item, calls OpenAI and writes the result.
    """
    # 1. Check cache
    result = await db.execute(
        select(ShelfLifeCache).where(ShelfLifeCache.item_name_key == name_normalised)
    )
    cached = result.scalar_one_or_none()
    if cached:
        return cached.shelf_life_days

    # 2. Cache miss — infer via LLM
    try:
        days = await infer_shelf_life_days(name_normalised)
    except (ValueError, Exception):
        # If OpenAI call fails or returns garbage, use default.
        # In Step 9 we'd log this for monitoring / manual review.
        days = _DEFAULT_FALLBACK_DAYS

    # 3. Write to cache so future requests skip the LLM
    entry = ShelfLifeCache(
        item_name_key=name_normalised,
        shelf_life_days=days,
        source_model=_MODEL_TAG,
    )
    db.add(entry)
    await db.commit()
    return days


def compute_inferred_expiry(added_on: date, shelf_life_days: int) -> date:
    """Pure function — added_at + shelf life = inferred expiry."""
    return added_on + timedelta(days=shelf_life_days)
