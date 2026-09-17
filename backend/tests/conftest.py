"""Test configuration: fixtures and test database setup."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

import os

# Use DATABASE_URL from environment if available (e.g. Postgres in CI), otherwise SQLite
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_darukaa.db")
connect_args = {"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args=connect_args,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables for tests (SQLite, no PostGIS)."""
    # For SQLite testing, we need to handle the geometry column differently
    # We'll create tables without the geometry column for unit tests
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    import os

    if os.path.exists("test_darukaa.db"):
        os.remove("test_darukaa.db")


@pytest.fixture
def db():
    """Provide a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client():
    """Provide a test HTTP client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Register and return a test user with token."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "TestPassword123",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(registered_user):
    """Return Authorization headers for authenticated requests."""
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}
