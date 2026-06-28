import pytest
from backend.models.models import User, Category, Source, Article, Bookmark, ArticleStatus, UserRole


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(
        id="test-id-1",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed123",
        full_name="Test User",
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()

    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    fetched = result.scalar_one()
    assert fetched.email == "test@example.com"
    assert fetched.is_active is True


@pytest.mark.asyncio
async def test_create_category(db_session):
    cat = Category(name="Technology", slug="technology")
    db_session.add(cat)
    await db_session.commit()

    from sqlalchemy import select
    result = await db_session.execute(select(Category).where(Category.slug == "technology"))
    assert result.scalar_one() is not None


@pytest.mark.asyncio
async def test_create_article(db_session):
    cat = Category(name="General", slug="general")
    src = Source(name="bbc", feed_url="http://feeds.bbci.co.uk/news/rss.xml")
    db_session.add_all([cat, src])
    await db_session.commit()

    article = Article(
        title="Test Article",
        slug="test-article",
        summary="A test summary",
        content="Full content here",
        status=ArticleStatus.PUBLISHED,
        category_id=cat.id,
        source_id=src.id,
    )
    db_session.add(article)
    await db_session.commit()

    from sqlalchemy import select
    result = await db_session.execute(select(Article).where(Article.slug == "test-article"))
    fetched = result.scalar_one()
    assert fetched.title == "Test Article"
    assert fetched.view_count == 0


@pytest.mark.asyncio
async def test_bookmark_relationship(db_session):
    user = User(id="test-id-2", email="user@test.com", username="bookmarkuser", hashed_password="hash")
    cat = Category(name="General", slug="general")
    src = Source(name="bbc", feed_url="http://feeds.bbci.co.uk/news/rss.xml")
    db_session.add_all([user, cat, src])
    await db_session.commit()

    article = Article(
        title="Bookmarkable",
        slug="bookmarkable",
        status=ArticleStatus.PUBLISHED,
        category_id=cat.id,
        source_id=src.id,
    )
    db_session.add(article)
    await db_session.commit()

    bm = Bookmark(user_id=user.id, article_id=article.id, folder="favorites")
    db_session.add(bm)
    await db_session.commit()

    from sqlalchemy import select
    result = await db_session.execute(
        select(Bookmark).where(Bookmark.user_id == user.id)
    )
    bookmarks = result.scalars().all()
    assert len(bookmarks) == 1
    assert bookmarks[0].folder == "favorites"
    assert bookmarks[0].article.title == "Bookmarkable"
