import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app import models
from app.operations import OperationType

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test_integration.db",
)

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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


def test_create_read_update_delete_calculation():
    # register and login to obtain token
    user_payload = {"username": "tester", "email": "tester@example.com", "password": "secret123"}
    r = client.post("/users/register", json=user_payload)
    assert r.status_code == 201

    login_payload = {"username": "tester", "password": "secret123"}
    r = client.post("/users/login", json=login_payload)
    assert r.status_code == 200
    token = r.json()["access_token"]
    refresh = r.json().get("refresh_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    payload = {"a": 20, "b": 4, "type": OperationType.Divide.value}
    r = client.post("/calculations", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["result"] == 5
    calc_id = data["id"]

    # Read
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == calc_id

    # Update (change operands)
    payload_upd = {"a": 10, "b": 2, "type": OperationType.Multiply.value}
    r = client.put(f"/calculations/{calc_id}", json=payload_upd, headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["result"] == 20

    # Delete
    r = client.delete(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 204

    # ensure 404 after delete
    r = client.get(f"/calculations/{calc_id}", headers=headers)
    assert r.status_code == 404


def test_refresh_and_logout_flow():
    # register and login
    user_payload = {"username": "refreshuser", "email": "refresh@example.com", "password": "secret123"}
    r = client.post("/users/register", json=user_payload)
    assert r.status_code == 201

    login_payload = {"username": "refreshuser", "password": "secret123"}
    r = client.post("/users/login", json=login_payload)
    assert r.status_code == 200
    access = r.json()["access_token"]
    refresh_token = r.json().get("refresh_token")
    assert refresh_token

    # exchange refresh token for new access token
    r = client.post("/users/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert r.json().get("access_token")

    # logout (requires access token) and provide refresh token to revoke
    headers = {"Authorization": f"Bearer {access}"}
    r = client.post("/users/logout", json={"refresh_token": refresh_token}, headers=headers)
    assert r.status_code == 200

    # using refresh token after logout should fail
    r = client.post("/users/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401


def test_list_and_revoke_tokens_by_user_and_admin():
    # register user and login to get refresh token
    user_payload = {"username": "tokenuser", "email": "token@example.com", "password": "secret123"}
    r = client.post("/users/register", json=user_payload)
    assert r.status_code == 201

    r = client.post("/users/login", json={"username": "tokenuser", "password": "secret123"})
    assert r.status_code == 200
    refresh_token = r.json().get("refresh_token")
    assert refresh_token

    # list tokens for current user using access token
    access = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}
    r = client.get("/users/me/tokens", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    token_id = data[0]["id"]

    # revoke token by id
    r = client.delete(f"/users/me/tokens/{token_id}", headers=headers)
    assert r.status_code == 200

    # admin revoke all tokens for user
    # create admin and elevate role
    r = client.post("/users/", json={"username": "admin2", "email": "admin2@example.com", "password": "adminpass"})
    assert r.status_code == 201
    db = next(override_get_db())
    admin = db.query(models.User).filter(models.User.username == "admin2").first()
    admin.role = "admin"
    db.add(admin)
    db.commit()

    r = client.post("/users/login", json={"username": "admin2", "password": "adminpass"})
    assert r.status_code == 200
    admin_access = r.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {admin_access}"}

    r = client.post(f"/users/tokenuser/revoke_all", headers=headers_admin)
    assert r.status_code == 200


def test_admin_list_per_user_and_revoke_by_token():
    # create user and login to obtain token
    r = client.post("/users/register", json={"username": "peruser", "email": "peruser@example.com", "password": "pw12345"})
    assert r.status_code == 201

    r = client.post("/users/login", json={"username": "peruser", "password": "pw12345"})
    assert r.status_code == 200
    refresh_token = r.json().get("refresh_token")
    assert refresh_token

    # create admin and elevate
    r = client.post("/users/", json={"username": "admin3", "email": "admin3@example.com", "password": "adminpass"})
    assert r.status_code == 201
    db = next(override_get_db())
    admin = db.query(models.User).filter(models.User.username == "admin3").first()
    admin.role = "admin"
    db.add(admin)
    db.commit()

    r = client.post("/users/login", json={"username": "admin3", "password": "adminpass"})
    assert r.status_code == 200
    admin_access = r.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {admin_access}"}

    # admin list tokens for the created user
    r = client.get("/admin/users/peruser/tokens", headers=headers_admin)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

    # admin revoke by token string
    r = client.post("/admin/tokens/revoke", json={"refresh_token": refresh_token}, headers=headers_admin)
    assert r.status_code == 200

    # token should be unusable afterwards
    r = client.post("/users/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401


def test_invalid_division_by_zero_returns_422():
    # authenticate
    user_payload = {"username": "tester2", "email": "tester2@example.com", "password": "secret123"}
    r = client.post("/users/register", json=user_payload)
    assert r.status_code == 201
    login_payload = {"username": "tester2", "password": "secret123"}
    r = client.post("/users/login", json=login_payload)
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"a": 1, "b": 0, "type": OperationType.Divide.value}
    r = client.post("/calculations", json=payload, headers=headers)
    # pydantic validation on CalculationCreate should reject division by zero
    assert r.status_code in (400, 422)
