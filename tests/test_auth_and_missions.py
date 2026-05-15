from __future__ import annotations

import uuid

import pytest


async def _register_and_login(client, *, email: str, password: str) -> str:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User", "role": "operator"},
    )
    assert reg.status_code in (201, 400), reg.text

    login = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_auth_me_and_missions_happy_path(client):
    email = f"test-{uuid.uuid4()}@example.com"
    password = "passw0rd-123"

    token = await _register_and_login(client, email=email, password=password)
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email.lower()

    created = await client.post(
        "/api/v1/missions",
        json={"title": "Test Mission", "description": "desc", "priority": 1, "drone_id": "dji-m3e", "waypoints": {}},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    mission_id = created.json()["id"]

    listed = await client.get("/api/v1/missions", headers=headers)
    assert listed.status_code == 200
    assert any(m["id"] == mission_id for m in listed.json())
