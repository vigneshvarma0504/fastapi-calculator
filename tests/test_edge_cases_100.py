"""Edge case tests to reach 100% coverage."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import SessionLocal, Base, get_db
from app import models
from unittest.mock import patch

# Isolated sqlite DB for this module
TEST_DATABASE_URL = "sqlite:///./test_edge_cases.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def cleanup_user(username: str):
    """Helper to clean up test users."""
    db = TestingSessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            db.query(models.Calculation).filter(models.Calculation.user_id == user.id).delete()
            from app.models import RefreshToken
            db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_refresh_with_jwt_decode_exception():
    """Test refresh endpoint when JWT decode raises an exception (lines 254-255)."""
    # Send a malformed token that will cause JWT decode to fail
    response = client.post(
        "/users/refresh",
        json={"refresh_token": "clearly.invalid.jwt"}
    )
    # Should return 400 or 401
    assert response.status_code in [400, 401]


def test_revoke_nonexistent_token():
    """Test revoking a token that doesn't exist in the database (line 282)."""
    cleanup_user("revokeuser2")
    
    # Register and login
    client.post(
        "/users/register",
        json={
            "username": "revokeuser2",
            "email": "revokeuser2@example.com",
            "password": "password123"
        }
    )
    
    login_response = client.post(
        "/users/login",
        json={
            "username": "revokeuser2",
            "password": "password123"
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # Try to revoke a completely fake token
    response = client.post(
        "/users/revoke",
        json={"refresh_token": "nonexistent_token_12345"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Should return 404 because token not found
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    cleanup_user("revokeuser2")
