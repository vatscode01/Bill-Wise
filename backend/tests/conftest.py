import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_billwise.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import user, bill, subscription  # noqa: F401 registers tables on Base.metadata

TEST_DB_URL = "sqlite:///./test_billwise.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def _fresh_database():
    """Arrange: give every test a clean database. Act/Assert happen in the test itself."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Registers+logs in a fresh user, returns (headers, user_email) ready to use."""
    def _make(email="user@example.com", password="password123"):
        client.post("/auth/register", json={"email": email, "password": password})
        r = client.post("/auth/login", json={"email": email, "password": password})
        token = r.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _make
