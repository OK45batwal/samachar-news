"""Integration tests for auth endpoints — profile creation and user info."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.config import settings
from backend.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite://"

needs_st = pytest.mark.skipif(
    not settings.SUPERTOKENS_CONNECTION_URI,
    reason="SuperTokens core not running",
)


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


@needs_st
@pytest.mark.asyncio
async def test_get_profile_unauthorized(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@needs_st
@pytest.mark.asyncio
async def test_create_profile_unauthorized(client):
    resp = await client.post("/api/auth/profile", json={
        "email": "test@test.com",
        "username": "testuser",
    })
    assert resp.status_code == 401
