from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm import build_shelf_life_prompt


# ── Pure function tests ─────────────────────────────────────────────

def test_prompt_contains_item_name():
    """Prompt builder includes the item name in the user message."""
    messages = build_shelf_life_prompt("chicken breast")
    user_content = messages[1]["content"]
    assert "chicken breast" in user_content


def test_prompt_has_system_role():
    """System message is first."""
    messages = build_shelf_life_prompt("milk")
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_prompt_enforces_integer_only():
    """System prompt forbids extra text — critical for parsing."""
    messages = build_shelf_life_prompt("apple")
    system = messages[0]["content"]
    assert "only the integer" in system.lower()


# ── Integration tests with OpenAI mocked ────────────────────────────

async def _register(client) -> dict:
    res = await client.post("/auth/register", json={
        "email": "shelf@example.com",
        "password": "password123",
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def test_cache_miss_calls_llm_and_writes_cache(client):
    """First time we add 'apple', LLM is called and result is cached."""
    headers = await _register(client)

    with patch("app.services.shelf_life.infer_shelf_life_days",
               new=AsyncMock(return_value=7)) as mock_llm:
        res = await client.post("/pantry/items",
            json={"name": "Apple"}, headers=headers)

        assert res.status_code == 201
        assert mock_llm.call_count == 1
        assert res.json()["inferred_expiry"] is not None


async def test_cache_hit_skips_llm(client):
    """Second 'apple' add reuses the cached shelf life — no LLM call."""
    headers = await _register(client)

    # Prime the cache
    with patch("app.services.shelf_life.infer_shelf_life_days",
               new=AsyncMock(return_value=7)):
        await client.post("/pantry/items", json={"name": "Apple"}, headers=headers)

    # Second add — LLM should NOT be called
    with patch("app.services.shelf_life.infer_shelf_life_days",
               new=AsyncMock(return_value=999)) as mock_llm:
        res = await client.post("/pantry/items",
            json={"name": "apple"},  # different case — must still hit cache
            headers=headers)

        assert res.status_code == 201
        assert mock_llm.call_count == 0   # cache hit, no LLM call


async def test_expiry_provided_skips_llm(client):
    """If user provides expiry_date, LLM is never called."""
    headers = await _register(client)

    with patch("app.services.shelf_life.infer_shelf_life_days",
               new=AsyncMock(return_value=7)) as mock_llm:
        res = await client.post("/pantry/items", json={
            "name": "Bread",
            "expiry_date": "2026-12-31",
        }, headers=headers)

        assert res.status_code == 201
        assert mock_llm.call_count == 0


async def test_llm_failure_falls_back_gracefully(client):
    """If OpenAI throws, we fall back to default and still succeed."""
    headers = await _register(client)

    with patch("app.services.shelf_life.infer_shelf_life_days",
               new=AsyncMock(side_effect=Exception("OpenAI down"))):
        res = await client.post("/pantry/items",
            json={"name": "Yoghurt"}, headers=headers)

        assert res.status_code == 201
        assert res.json()["inferred_expiry"] is not None  # default applied
        