import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _auth_headers(client) -> dict:
    """Register a user and return auth headers."""
    res = await client.post("/auth/register", json={
        "email": "prefs@example.com",
        "password": "password123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_default_preferences_empty(client):
    """New user starts with empty dietary prefs."""
    headers = await _auth_headers(client)
    res = await client.get("/users/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["dietary_prefs"] == {}


async def test_update_preferences(client):
    headers = await _auth_headers(client)
    res = await client.patch("/users/me/preferences", headers=headers, json={
        "high_protein": True,
        "spice_level": 4,
        "allergens": ["nuts", "dairy"],
    })
    assert res.status_code == 200
    prefs = res.json()["dietary_prefs"]
    assert prefs["high_protein"] is True
    assert prefs["spice_level"] == 4
    assert "nuts" in prefs["allergens"]


async def test_partial_update_preserves_existing(client):
    """
    PATCH only spice_level — allergens set earlier must survive.
    This is the merge test — proves we're not replacing the whole object.
    """
    headers = await _auth_headers(client)

    # First set allergens
    await client.patch("/users/me/preferences", headers=headers, json={
        "allergens": ["shellfish"],
    })

    # Then update only spice level
    await client.patch("/users/me/preferences", headers=headers, json={
        "spice_level": 2,
    })

    res = await client.get("/users/me", headers=headers)
    prefs = res.json()["dietary_prefs"]
    assert prefs["spice_level"] == 2
    assert prefs["allergens"] == ["shellfish"]  # must still be here


async def test_unknown_field_rejected(client):
    """extra='forbid' means unknown fields return 422."""
    headers = await _auth_headers(client)
    res = await client.patch("/users/me/preferences", headers=headers, json={
        "favourite_color": "green",  # not a real field
    })
    assert res.status_code == 422


async def test_preferences_requires_auth(client):
    res = await client.patch("/users/me/preferences", json={"spice_level": 3})
    assert res.status_code == 401
    