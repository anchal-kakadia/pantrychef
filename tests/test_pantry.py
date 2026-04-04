import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _register_and_login(client) -> str:
    """Helper — register a user and return their auth token."""
    res = await client.post("/auth/register", json={
        "email": "pantry@example.com",
        "password": "password123",
    })
    return res.json()["access_token"]


@pytest.fixture
async def auth_client(client):
    """An HTTP client with Authorization header already set."""
    token = await _register_and_login(client)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


async def test_add_item(auth_client):
    res = await auth_client.post("/pantry/items", json={
        "name": "Chicken Breast",
        "quantity": 500,
        "unit": "g",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Chicken Breast"
    assert data["name_normalised"] == "chicken breast"
    assert data["expiry_date"] is None      # no expiry provided
    assert data["inferred_expiry"] is None  # LLM not wired yet


async def test_list_items(auth_client):
    await auth_client.post("/pantry/items", json={"name": "Milk"})
    await auth_client.post("/pantry/items", json={"name": "Eggs"})
    res = await auth_client.get("/pantry/items")
    assert res.status_code == 200
    assert len(res.json()) == 2


async def test_update_item(auth_client):
    create = await auth_client.post("/pantry/items", json={
        "name": "Butter", "quantity": 250, "unit": "g"
    })
    item_id = create.json()["id"]
    res = await auth_client.patch(f"/pantry/items/{item_id}", json={"quantity": 100})
    assert res.status_code == 200
    assert res.json()["quantity"] == 100
    assert res.json()["unit"] == "g"   # unchanged field preserved


async def test_delete_item(auth_client):
    create = await auth_client.post("/pantry/items", json={"name": "Yoghurt"})
    item_id = create.json()["id"]
    res = await auth_client.delete(f"/pantry/items/{item_id}")
    assert res.status_code == 204
    # Deleted item should not appear in list
    items = await auth_client.get("/pantry/items")
    assert all(i["id"] != item_id for i in items.json())


async def test_get_item_not_found(auth_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = await auth_client.get(f"/pantry/items/{fake_id}")
    assert res.status_code == 404


async def test_cannot_access_other_users_item(client):
    """User A cannot access User B's items."""
    # Register user A
    res_a = await client.post("/auth/register", json={
        "email": "usera@example.com", "password": "password123"
    })
    token_a = res_a.json()["access_token"]

    # User A adds an item
    item = await client.post("/pantry/items", json={"name": "Apple"},
        headers={"Authorization": f"Bearer {token_a}"})
    item_id = item.json()["id"]

    # Register user B
    res_b = await client.post("/auth/register", json={
        "email": "userb@example.com", "password": "password123"
    })
    token_b = res_b.json()["access_token"]

    # User B tries to access user A's item — must get 404, not the item
    res = await client.get(f"/pantry/items/{item_id}",
        headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404
    