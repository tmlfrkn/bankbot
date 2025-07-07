import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.models import User
from app.security import get_password_hash

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# -----------------------------------------------------------------------------
# Database utilities for tests
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory SQLite DB for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide session to tests
    async with async_session() as session:
        yield session

    # Drop tables after tests
    await engine.dispose()


@pytest.fixture(scope="module")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Override get_db dependency and provide HTTP client."""
    async def _get_test_db():
        async with test_db.begin():
            yield test_db
    # Override dependency
    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

    # Remove override after tests
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
async def test_user(test_db: AsyncSession):
    """Create a test user in the DB."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        access_level=3,
        role="Risk Analyst",
    )
    test_db.add(user)
    await test_db.commit()
    return user


@pytest.mark.anyio
async def test_login_success(client: AsyncClient, test_user: User):
    response = await client.post("/auth/login", json={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_failure_wrong_password(client: AsyncClient, test_user: User):
    response = await client.post("/auth/login", json={"username": "testuser", "password": "wrongpass"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_failure_unknown_user(client: AsyncClient):
    response = await client.post("/auth/login", json={"username": "unknown", "password": "nope"})
    assert response.status_code == 401 