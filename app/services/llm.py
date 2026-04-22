from openai import AsyncOpenAI

from app.config import settings

# Single client instance — reused across all requests.
# AsyncOpenAI is the async version; connects to OpenAI API.
_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    """
    Lazy singleton. Created on first call, reused after.
    Making this a function (not module-level) means tests can
    patch/override it easily without triggering real API calls on import.
    """
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


# ── Prompts (versioned constants) ─────────────────────────────────────

# v1 — Shelf life inference
# Design: deterministic, minimal tokens, integer-parseable output.
# temperature=0 so the same item always returns the same value.
SHELF_LIFE_SYSTEM_PROMPT = """You are a food science assistant.
When given the name of a food or grocery item, respond with a single integer \
representing the typical shelf life in days when stored correctly at home.
Do not include units, explanations, or any other text — only the integer.
If the item name is ambiguous, return the conservative (shorter) estimate."""


def build_shelf_life_prompt(item_name: str) -> list[dict]:
    """
    Returns the messages list in OpenAI's format.
    Kept as a pure function so it's easy to unit test without
    mocking OpenAI at all.
    """
    return [
        {"role": "system", "content": SHELF_LIFE_SYSTEM_PROMPT},
        {"role": "user", "content": f"What is the typical shelf life in days of: {item_name}"},
    ]


async def infer_shelf_life_days(item_name: str) -> int:
    """
    Calls OpenAI and returns shelf life as an int.
    Raises ValueError if the response can't be parsed as a positive integer.
    """
    client = get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",          # cheap, fast, accurate enough for this task
        messages=build_shelf_life_prompt(item_name),
        temperature=0,                   # deterministic — same item → same answer
        max_tokens=10,                   # we only need "7" or similar
    )
    raw = response.choices[0].message.content.strip()
    days = int(raw)                      # raises ValueError if not parseable

    if days <= 0 or days > 3650:
        raise ValueError(f"Implausible shelf life: {days} days")
    return days
