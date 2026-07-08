"""Integration tests for articles + bookmarks CRUD."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.config import settings
from backend.database import Base, get_db
from backend.models.models import Article, ArticleStatus, Category, Source

TEST_DB_URL = "sqlite+aiosqlite://"

needs_st = pytest.mark.skipif(
    not settings.SUPERTOKENS_CONNECTION_URI,
    reason="SuperTokens core not running",
)


@pytest_asyncio.fixture
async def seeded_client():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        cat = Category(name="Test", slug="test")
        src = Source(name="Test Source", feed_url="http://example.com/rss")
        session.add_all([cat, src])
        await session.commit()

        for i in range(5):
            a = Article(
                title=f"Test Article {i}",
                slug=f"test-article-{i}",
                summary=f"Summary {i}",
                content=f"Content {i}",
                status=ArticleStatus.PUBLISHED,
                category_id=cat.id,
                source_id=src.id,
            )
            session.add(a)
        await session.commit()

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
async def test_list_articles(seeded_client):
    resp = await seeded_client.get("/api/news/?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["articles"]) == 5


@pytest.mark.asyncio
async def test_get_article_by_id(seeded_client):
    resp = await seeded_client.get("/api/news/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["category"]["slug"] == "test"


@pytest.mark.asyncio
async def test_get_nonexistent_article(seeded_client):
    resp = await seeded_client.get("/api/news/999999")
    assert resp.status_code == 404


@needs_st
@pytest.mark.asyncio
async def test_bookmark_unauthorized(seeded_client):
    resp = await seeded_client.post("/api/bookmarks/", json={"article_id": 1})
    assert resp.status_code == 401
