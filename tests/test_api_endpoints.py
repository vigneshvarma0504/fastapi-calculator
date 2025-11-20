import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test_integration.db",
)

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_user_success():
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "supersecret",
    }
    resp = client.post("/users/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_username_and_email_must_be_unique():
    payload1 = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "supersecret",
    }
    payload2 = {
        "username": "bob",  # same username
        "email": "bob2@example.com",
        "password": "supersecret",
    }

    r1 = client.post("/users/", json=payload1)
    assert r1.status_code == 201

    r2 = client.post("/users/", json=payload2)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"]


def test_list_users_returns_created_users():
    # ensure at least one user exists
    payload = {
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "supersecret",
    }
    r = client.post("/users/", json=payload)
    assert r.status_code == 201

    # call GET /users/ to hit list_users in app.main
    resp = client.get("/users/")
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, list)
    usernames = [u["username"] for u in data]
    assert "charlie" in usernames
