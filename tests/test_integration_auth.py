"""Integration tests for auth endpoints — register, login, refresh, profile."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "new@test.com",
        "password": "ValidPass1",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["username"] == "newuser"
    assert data["user"]["email"] == "new@test.com"
    assert "id" in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_user(client):
    await client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "dup@test.com",
        "password": "ValidPass1",
    })
    resp = await client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "other@test.com",
        "password": "ValidPass1",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client):
    resp = await client.post("/api/auth/register", json={
        "username": "weakuser",
        "email": "weak@test.com",
        "password": "short",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={
        "username": "loginuser",
        "email": "login@test.com",
        "password": "MyPass123",
    })
    resp = await client.post("/api/auth/login", json={
        "username": "loginuser",
        "password": "MyPass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "username": "wrongpw",
        "email": "wrong@test.com",
        "password": "MyPass123",
    })
    resp = await client.post("/api/auth/login", json={
        "username": "wrongpw",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    await client.post("/api/auth/register", json={
        "username": "refreshuser",
        "email": "refresh@test.com",
        "password": "MyPass123",
    })
    login = (await client.post("/api/auth/login", json={
        "username": "refreshuser",
        "password": "MyPass123",
    })).json()
    resp = await client.post("/api/auth/refresh", json={
        "refresh_token": login["refresh_token"],
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_get_profile(client):
    await client.post("/api/auth/register", json={
        "username": "profileuser",
        "email": "profile@test.com",
        "password": "MyPass123",
    })
    login = (await client.post("/api/auth/login", json={
        "username": "profileuser",
        "password": "MyPass123",
    })).json()
    resp = await client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {login['access_token']}",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "profileuser"
    assert data["email"] == "profile@test.com"


@pytest.mark.asyncio
async def test_get_profile_unauthorized(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401
