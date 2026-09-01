import pytest
import pytest_asyncio

from backend.database import init_db
from backend.seed import seed_database


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_test_database():
    await init_db()
    await seed_database()
