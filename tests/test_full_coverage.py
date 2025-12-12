# Ensure pytest is imported first
import pytest
import uuid
# Add fixture to reset DB before each test
@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

# Helper for unique user
def unique_user(prefix, password="adminpass"):
    u = str(uuid.uuid4())[:8]
    return {
        "username": f"{prefix}_{u}",
        "email": f"{prefix}_{u}@example.com",
        "password": password
    }
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from app import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_coverage.db")
if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

# --- Admin-only endpoints ---
def test_admin_endpoints_and_errors():
    # Create admin
    admin_payload = unique_user("admin100x")
    r = client.post("/users/", json=admin_payload)
    db = next(override_get_db())
    admin = db.query(models.User).filter_by(username=admin_payload["username"]).first()
    assert admin is not None
    admin.role = "admin"
    db.add(admin)
    db.commit()
    # Login as admin
    r = client.post("/users/login", json={"username": admin_payload["username"], "password": admin_payload["password"]})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # List users
    r = client.get("/users/", headers=headers)
    assert r.status_code == 200
    # List all tokens
    r = client.get("/admin/tokens", headers=headers)
    assert r.status_code == 200
    # List tokens for user
    r = client.get(f"/admin/users/{admin_payload['username']}/tokens", headers=headers)
    assert r.status_code == 200
    # Revoke all tokens for user
    r = client.post(f"/users/{admin_payload['username']}/revoke_all", headers=headers)
    assert r.status_code == 200
    # List users with token count
    r = client.get("/admin/users", headers=headers)
    assert r.status_code == 200
    # Set user role
    r = client.post(f"/users/{admin_payload['username']}/role", json={"role": "user"}, headers=headers)
    assert r.status_code == 200
    # Try admin endpoint as non-admin
    user_payload = unique_user("notadminx", password="pass1234")
    r = client.post("/users/", json=user_payload)
    assert r.status_code == 201
    r = client.post("/users/login", json={"username": user_payload["username"], "password": user_payload["password"]})
    token2 = r.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    r = client.get("/admin/tokens", headers=headers2)
    assert r.status_code == 403

# --- Calculation error branches ---
def test_calculation_not_found_and_delete():
    # Register and login
    user_payload = unique_user("calcuser", password="pass1234")
    r = client.post("/users/register", json=user_payload)
    assert r.status_code == 201
    r = client.post("/users/login", json={"username": user_payload["username"], "password": user_payload["password"]})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Get non-existent calculation
    r = client.get("/calculations/9999", headers=headers)
    assert r.status_code == 404
    # Update non-existent calculation
    payload = {"a": 1, "b": 2, "type": "add"}
    r = client.put("/calculations/9999", json=payload, headers=headers)
    assert r.status_code in (404, 422)
    # Delete non-existent calculation
    r = client.delete("/calculations/9999", headers=headers)
    assert r.status_code == 404

# --- Token revoke and error branches ---
def test_token_revoke_errors():
    # Register and login
    user_payload = unique_user("tokuser", password="pass1234")
    r = client.post("/users/register", json=user_payload)
    assert r.status_code == 201
    r = client.post("/users/login", json={"username": user_payload["username"], "password": user_payload["password"]})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Revoke with invalid token
    r = client.post("/users/me/revoke", json={"refresh_token": "badtoken"}, headers=headers)
    assert r.status_code in (404, 422)
    # List my tokens (should work, even if empty)
    r = client.get("/users/me/tokens", headers=headers)
    assert r.status_code == 200
    # Revoke by id (not found)
    r = client.delete("/users/me/tokens/9999", headers=headers)
    assert r.status_code == 404

# --- Auth error branches ---
def test_auth_errors():
    # Invalid login
    r = client.post("/users/login", json={"username": "nope", "password": "bad"})
    assert r.status_code == 401
    # Access protected endpoint with no token
    r = client.get("/calculations")
    assert r.status_code == 401
    # Access protected endpoint with bad token
    r = client.get("/calculations", headers={"Authorization": "Bearer badtoken"})
    assert r.status_code == 401
    # Refresh with missing token
    r = client.post("/users/refresh", json={})
    assert r.status_code in (400, 422)
    # Refresh with invalid token
    r = client.post("/users/refresh", json={"refresh_token": "badtoken"})
    assert r.status_code == 400 or r.status_code == 401
    # Logout with missing token
    r = client.post("/users/logout", json={}, headers={"Authorization": "Bearer badtoken"})
    assert r.status_code in (400, 401)
    # Admin revoke by token (not found)
    # First, login as admin
    admin_payload = unique_user("admin101")
    r = client.post("/users/", json=admin_payload)
    db = next(override_get_db())
    admin = db.query(models.User).filter_by(username=admin_payload["username"]).first()
    admin.role = "admin"
    db.add(admin)
    db.commit()
    r = client.post("/users/login", json={"username": admin_payload["username"], "password": admin_payload["password"]})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/admin/tokens/revoke", json={"refresh_token": "notarealtoken"}, headers=headers)
    assert r.status_code == 404
