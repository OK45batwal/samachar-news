import pytest
from httpx import ASGITransport, AsyncClient

from backend.app import app


@pytest.mark.asyncio
async def test_get_profile_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/auth/me")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_register_and_login_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = "testuser_verify@samachar.news"
        pwd = "SecureTestPassword123!"

        # Register
        reg_res = await client.post("/api/auth/register", json={"email": email, "password": pwd, "full_name": "Test User"})
        assert reg_res.status_code in [201, 409]

        # Login
        login_res = await client.post("/api/auth/login", json={"email": email, "password": pwd})
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        token = data["access_token"]

        # Get profile with Bearer
        prof_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert prof_res.status_code == 200
        assert prof_res.json()["email"] == email

        # Get WS token
        ws_res = await client.get("/api/auth/ws-token", headers={"Authorization": f"Bearer {token}"})
        assert ws_res.status_code == 200
        assert "token" in ws_res.json()
