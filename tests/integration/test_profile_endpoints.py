"""
Integration tests for user profile management endpoints.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import Base, get_db
from app.models import User
from app.security import hash_password


# Test database setup
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///./test_profile_integration.db",
)

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Setup and teardown database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    """Override database dependency."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ensure DB override is applied for this module and cleaned up after.
@pytest.fixture(scope="function", autouse=True)
def apply_db_override():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db_session():
    """Get database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testprofileuser",
        email="testprofile@example.com",
        password_hash=hash_password("TestPass123!"),
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    client = TestClient(app)
    response = client.post(
        "/users/login",
        json={"username": "testprofileuser", "password": "TestPass123!"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetCurrentUserInfo:
    """Test GET /users/me endpoint."""

    def test_get_current_user_success(self, test_user, auth_headers):
        """Test getting current user info successfully."""
        client = TestClient(app)
        response = client.get("/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testprofileuser"
        assert data["email"] == "testprofile@example.com"
        assert data["role"] == "user"
        assert "id" in data
        assert "password_hash" not in data  # Should not expose password

    def test_get_current_user_no_auth(self):
        """Test getting current user without authentication."""
        client = TestClient(app)
        response = client.get("/users/me")
        
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        client = TestClient(app)
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestUpdateUserProfile:
    """Test PATCH /users/me endpoint."""

    def test_update_username_success(self, test_user, auth_headers, db_session):
        """Test updating username successfully."""
        client = TestClient(app)
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={"username": "newusername"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newusername"
        assert data["email"] == "testprofile@example.com"
        
        # Verify in database
        db_session.refresh(test_user)
        assert test_user.username == "newusername"

    def test_update_email_success(self, test_user, auth_headers, db_session):
        """Test updating email successfully."""
        client = TestClient(app)
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={"email": "newemail@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testprofileuser"
        assert data["email"] == "newemail@example.com"
        
        # Verify in database
        db_session.refresh(test_user)
        assert test_user.email == "newemail@example.com"

    def test_update_both_fields_success(self, test_user, auth_headers, db_session):
        """Test updating both username and email successfully."""
        client = TestClient(app)
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={
                "username": "newusername",
                "email": "newemail@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newusername"
        assert data["email"] == "newemail@example.com"
        
        # Verify in database
        db_session.refresh(test_user)
        assert test_user.username == "newusername"
        assert test_user.email == "newemail@example.com"

    def test_update_username_already_taken(self, test_user, auth_headers, db_session):
        """Test updating username to one that's already taken."""
        # Create another user
        other_user = User(
            username="existinguser",
            email="existing@example.com",
            password_hash=hash_password("Pass123!"),
            role="user"
        )
        db_session.add(other_user)
        db_session.commit()
        
        client = TestClient(app)
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={"username": "existinguser"}
        )
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()

    def test_update_email_already_taken(self, test_user, auth_headers, db_session):
        """Test updating email to one that's already taken."""
        # Create another user
        other_user = User(
            username="existinguser",
            email="existing@example.com",
            password_hash=hash_password("Pass123!"),
            role="user"
        )
        db_session.add(other_user)
        db_session.commit()
        
        client = TestClient(app)
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={"email": "existing@example.com"}
        )
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()

    def test_update_no_auth(self):
        """Test updating profile without authentication."""
        client = TestClient(app)
        response = client.patch(
            "/users/me",
            json={"username": "newusername"}
        )
        
        assert response.status_code == 401

    def test_update_invalid_email(self, test_user, auth_headers):
        """Test updating with invalid email format."""
        client = TestClient(app)
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={"email": "not-an-email"}
        )
        
        assert response.status_code == 422


class TestChangePassword:
    """Test POST /users/me/change-password endpoint."""

    def test_change_password_success(self, test_user, auth_headers, db_session):
        """Test changing password successfully."""
        client = TestClient(app)
        response = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "TestPass123!",
                "new_password": "NewPass456@"
            }
        )
        
        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()
        
        # Verify can login with new password
        login_response = client.post(
            "/users/login",
            json={"username": "testprofileuser", "password": "NewPass456@"}
        )
        assert login_response.status_code == 200
        
        # Verify cannot login with old password
        old_login = client.post(
            "/users/login",
            json={"username": "testprofileuser", "password": "TestPass123!"}
        )
        assert old_login.status_code == 401

    def test_change_password_wrong_current(self, test_user, auth_headers):
        """Test changing password with wrong current password."""
        client = TestClient(app)
        response = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewPass456@"
            }
        )
        
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_same_as_current(self, test_user, auth_headers):
        """Test changing password to same as current (should fail validation)."""
        client = TestClient(app)
        response = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "TestPass123!",
                "new_password": "TestPass123!"
            }
        )
        
        # Should fail at schema validation level
        assert response.status_code == 422

    def test_change_password_weak_new(self, test_user, auth_headers):
        """Test changing password to weak password."""
        client = TestClient(app)
        response = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={
                "current_password": "TestPass123!",
                "new_password": "weak"
            }
        )
        
        assert response.status_code == 422

    def test_change_password_no_auth(self):
        """Test changing password without authentication."""
        client = TestClient(app)
        response = client.post(
            "/users/me/change-password",
            json={
                "current_password": "TestPass123!",
                "new_password": "NewPass456@"
            }
        )
        
        assert response.status_code == 401

    def test_change_password_missing_fields(self, test_user, auth_headers):
        """Test changing password with missing fields."""
        client = TestClient(app)
        
        # Missing new_password
        response1 = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={"current_password": "TestPass123!"}
        )
        assert response1.status_code == 422
        
        # Missing current_password
        response2 = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={"new_password": "NewPass456@"}
        )
        assert response2.status_code == 422


class TestProfileIntegrationFlow:
    """Test complete profile management flows."""

    def test_complete_profile_update_flow(self, test_user, auth_headers, db_session):
        """Test complete flow: get profile -> update -> verify -> change password."""
        client = TestClient(app)
        
        # 1. Get current profile
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        original_data = response.json()
        
        # 2. Update profile
        update_response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={
                "username": "updateduser",
                "email": "updated@example.com"
            }
        )
        assert update_response.status_code == 200

        # Refresh token after username change
        relogin = client.post(
            "/users/login",
            json={"username": "updateduser", "password": "TestPass123!"}
        )
        assert relogin.status_code == 200
        new_headers = {"Authorization": f"Bearer {relogin.json()['access_token']}"}
        
        # 3. Verify update
        verify_response = client.get("/users/me", headers=new_headers)
        assert verify_response.status_code == 200
        updated_data = verify_response.json()
        assert updated_data["username"] == "updateduser"
        assert updated_data["email"] == "updated@example.com"
        
        # 4. Change password
        password_response = client.post(
            "/users/me/change-password",
            headers=new_headers,
            json={
                "current_password": "TestPass123!",
                "new_password": "NewPass456@"
            }
        )
        assert password_response.status_code == 200
        
        # 5. Login with new credentials
        login_response = client.post(
            "/users/login",
            json={"username": "updateduser", "password": "NewPass456@"}
        )
        assert login_response.status_code == 200
