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
        assert reg_res.status_code in [201, 400, 409]

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

        # Delete account
        del_res = await client.delete("/api/auth/account", headers={"Authorization": f"Bearer {token}"})
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"


@pytest.mark.asyncio
async def test_forgot_password_no_token_leak():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/auth/forgot-password", json={"email": "nonexistent@samachar.news"})
        assert res.status_code == 200
        data = res.json()
        assert "reset_token_dev" not in data


@pytest.mark.asyncio
async def test_otp_verification_rejects_unrequested_code():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/auth/verify-auth-otp", json={"email": "nobody@example.com", "otp": "123456"})
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_news_sync_requires_admin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/news/sync")
        assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_stats_alias_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/stats")
        assert res.status_code == 200
        data = res.json()
        assert "total_articles" in data
        assert "credibility_avg" in data

