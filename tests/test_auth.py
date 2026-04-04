import pytest

@pytest.mark.asyncio
async def test_register_success(client):
    res = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword123",
    })
    assert res.status_code == 201
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "password123"}
    await client.post("/auth/register", json=payload)
    res = await client.post("/auth/register", json=payload)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "user@example.com", "password": "correctpassword"
    })
    res = await client.post("/auth/token", data={
        "username": "user@example.com", "password": "wrongpassword"
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_auth(client):
    res = await client.get("/users/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    reg = await client.post("/auth/register", json={
        "email": "me@example.com", "password": "password123"
    })
    token = reg.json()["access_token"]
    res = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"