"""
End-to-end tests for user profile management flow.
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
    "sqlite:///./test_profile_e2e.db",
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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db_session():
    """Get database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestProfileE2E:
    """End-to-end tests for complete profile management workflows."""

    def test_complete_user_journey_with_profile(self, db_session: Session):
        """
        Test complete user journey:
        1. Register new user
        2. Login
        3. View profile
        4. Update username
        5. Update email
        6. Change password
        7. Logout and re-login with new password
        """
        client = TestClient(app)
        
        # Step 1: Register new user
        register_response = client.post(
            "/users/register",
            json={
                "username": "e2euser",
                "email": "e2e@example.com",
                "password": "InitialPass123!",
                "role": "user"
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["username"] == "e2euser"
        
        # Step 2: Login
        login_response = client.post(
            "/users/login",
            json={"username": "e2euser", "password": "InitialPass123!"}
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 3: View profile
        profile_response = client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["username"] == "e2euser"
        assert profile["email"] == "e2e@example.com"
        assert profile["role"] == "user"
        
        # Step 4: Update username
        update_username_response = client.patch(
            "/users/me",
            headers=headers,
            json={"username": "e2euser_updated"}
        )
        assert update_username_response.status_code == 200
        assert update_username_response.json()["username"] == "e2euser_updated"
        
        # Step 5: Update email
        # Re-login to get token tied to updated username
        relogin_after_username = client.post(
            "/users/login",
            json={"username": "e2euser_updated", "password": "InitialPass123!"}
        )
        assert relogin_after_username.status_code == 200
        headers = {"Authorization": f"Bearer {relogin_after_username.json()['access_token']}"}

        update_email_response = client.patch(
            "/users/me",
            headers=headers,
            json={"email": "e2e_updated@example.com"}
        )
        assert update_email_response.status_code == 200
        assert update_email_response.json()["email"] == "e2e_updated@example.com"
        
        # Step 6: Change password
        change_password_response = client.post(
            "/users/me/change-password",
            headers=headers,
            json={
                "current_password": "InitialPass123!",
                "new_password": "UpdatedPass456@"
            }
        )
        assert change_password_response.status_code == 200
        assert "success" in change_password_response.json()["message"].lower()
        
        # Step 7: Logout (clear token) and re-login with new credentials
        new_login_response = client.post(
            "/users/login",
            json={"username": "e2euser_updated", "password": "UpdatedPass456@"}
        )
        assert new_login_response.status_code == 200
        new_tokens = new_login_response.json()
        assert "access_token" in new_tokens
        
        # Verify old password doesn't work
        old_login_response = client.post(
            "/users/login",
            json={"username": "e2euser_updated", "password": "InitialPass123!"}
        )
        assert old_login_response.status_code == 401

    def test_profile_access_control(self, db_session: Session):
        """
        Test that users can only access and modify their own profiles.
        """
        client = TestClient(app)
        
        # Create two users
        user1 = User(
            username="user1",
            email="user1@example.com",
            password_hash=hash_password("User1Pass123!"),
            role="user"
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash=hash_password("User2Pass123!"),
            role="user"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Login as user1
        user1_login = client.post(
            "/users/login",
            json={"username": "user1", "password": "User1Pass123!"}
        )
        assert user1_login.status_code == 200
        user1_headers = {"Authorization": f"Bearer {user1_login.json()['access_token']}"}
        
        # Get user1's profile
        user1_profile = client.get("/users/me", headers=user1_headers)
        assert user1_profile.status_code == 200
        assert user1_profile.json()["username"] == "user1"
        
        # Update user1's username
        update_response = client.patch(
            "/users/me",
            headers=user1_headers,
            json={"username": "user1_updated"}
        )
        assert update_response.status_code == 200
        
        # Verify user2 still has original username
        user2_login = client.post(
            "/users/login",
            json={"username": "user2", "password": "User2Pass123!"}
        )
        user2_headers = {"Authorization": f"Bearer {user2_login.json()['access_token']}"}
        user2_profile = client.get("/users/me", headers=user2_headers)
        assert user2_profile.status_code == 200
        assert user2_profile.json()["username"] == "user2"

    def test_profile_update_with_calculations(self, db_session: Session):
        """
        Test that profile updates don't affect user's calculations.
        """
        client = TestClient(app)
        
        # Register and login
        register_response = client.post(
            "/users/register",
            json={
                "username": "calcuser",
                "email": "calc@example.com",
                "password": "CalcPass123!",
                "role": "user"
            }
        )
        assert register_response.status_code == 201
        
        login_response = client.post(
            "/users/login",
            json={"username": "calcuser", "password": "CalcPass123!"}
        )
        assert login_response.status_code == 200
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Create some calculations
        calc1 = client.post(
            "/calculations/",
            headers=headers,
            json={"a": 10, "b": 5, "type": "Add"}
        )
        assert calc1.status_code == 201
        
        calc2 = client.post(
            "/calculations/",
            headers=headers,
            json={"a": 20, "b": 4, "type": "Multiply"}
        )
        assert calc2.status_code == 201
        
        # Update profile
        profile_update = client.patch(
            "/users/me",
            headers=headers,
            json={"username": "calcuser_updated"}
        )
        assert profile_update.status_code == 200
        # Re-login after username change to get a fresh token
        relogin = client.post(
            "/users/login",
            json={"username": "calcuser_updated", "password": "CalcPass123!"}
        )
        assert relogin.status_code == 200
        headers = {"Authorization": f"Bearer {relogin.json()['access_token']}"}
        
        # Verify calculations still exist and belong to user
        calcs_response = client.get("/calculations/", headers=headers)
        assert calcs_response.status_code == 200
        calcs = calcs_response.json()
        assert len(calcs) >= 2
        
        # Find our calculations
        our_calcs = [c for c in calcs if c["a"] in [10, 20]]
        assert len(our_calcs) == 2

    def test_failed_password_change_preserves_access(self, db_session: Session):
        """
        Test that failed password change doesn't lock user out.
        """
        client = TestClient(app)
        
        # Register and login
        register_response = client.post(
            "/users/register",
            json={
                "username": "passuser",
                "email": "pass@example.com",
                "password": "OriginalPass123!",
                "role": "user"
            }
        )
        assert register_response.status_code == 201
        
        login_response = client.post(
            "/users/login",
            json={"username": "passuser", "password": "OriginalPass123!"}
        )
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Attempt to change password with wrong current password
        change_response = client.post(
            "/users/me/change-password",
            headers=headers,
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewPass456@"
            }
        )
        assert change_response.status_code == 400
        
        # Verify original password still works
        relogin_response = client.post(
            "/users/login",
            json={"username": "passuser", "password": "OriginalPass123!"}
        )
        assert relogin_response.status_code == 200
        
        # Verify profile is still accessible
        profile_response = client.get("/users/me", headers=headers)
        assert profile_response.status_code == 200

    def test_profile_update_unique_constraints(self, db_session: Session):
        """
        Test that username and email uniqueness is enforced across users.
        """
        client = TestClient(app)
        
        # Create first user
        user1 = User(
            username="uniqueuser1",
            email="unique1@example.com",
            password_hash=hash_password("User1Pass123!"),
            role="user"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Register second user
        register_response = client.post(
            "/users/register",
            json={
                "username": "uniqueuser2",
                "email": "unique2@example.com",
                "password": "User2Pass123!",
                "role": "user"
            }
        )
        assert register_response.status_code == 201
        
        # Login as second user
        login_response = client.post(
            "/users/login",
            json={"username": "uniqueuser2", "password": "User2Pass123!"}
        )
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Try to update to first user's username
        update_username = client.patch(
            "/users/me",
            headers=headers,
            json={"username": "uniqueuser1"}
        )
        assert update_username.status_code == 400
        assert "already taken" in update_username.json()["detail"].lower()
        
        # Try to update to first user's email
        update_email = client.patch(
            "/users/me",
            headers=headers,
            json={"email": "unique1@example.com"}
        )
        assert update_email.status_code == 400
        assert "already taken" in update_email.json()["detail"].lower()
        
        # Verify second user can update to their own current values
        update_own = client.patch(
            "/users/me",
            headers=headers,
            json={"username": "uniqueuser2", "email": "unique2@example.com"}
        )
        assert update_own.status_code == 200

    def test_multiple_password_changes(self, db_session: Session):
        """
        Test multiple consecutive password changes.
        """
        client = TestClient(app)
        
        # Register user
        register_response = client.post(
            "/users/register",
            json={
                "username": "multipassuser",
                "email": "multipass@example.com",
                "password": "Pass1",  # too short to fail (min length 6)
                "role": "user"
            }
        )
        # Password too short, use proper one
        register_response = client.post(
            "/users/register",
            json={
                "username": "multipassuser",
                "email": "multipass@example.com",
                "password": "Password1@",
                "role": "user"
            }
        )
        assert register_response.status_code == 201
        
        # Login
        login_response = client.post(
            "/users/login",
            json={"username": "multipassuser", "password": "Password1@"}
        )
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Change password 1st time
        change1 = client.post(
            "/users/me/change-password",
            headers=headers,
            json={"current_password": "Password1@", "new_password": "Password2@"}
        )
        assert change1.status_code == 200
        
        # Change password 2nd time
        change2 = client.post(
            "/users/me/change-password",
            headers=headers,
            json={"current_password": "Password2@", "new_password": "Password3@"}
        )
        assert change2.status_code == 200
        
        # Change password 3rd time
        change3 = client.post(
            "/users/me/change-password",
            headers=headers,
            json={"current_password": "Password3@", "new_password": "Password4@"}
        )
        assert change3.status_code == 200
        
        # Verify final password works
        final_login = client.post(
            "/users/login",
            json={"username": "multipassuser", "password": "Password4@"}
        )
        assert final_login.status_code == 200
        
        # Verify old passwords don't work
        for old_pass in ["Password1@", "Password2@", "Password3@"]:
            old_login = client.post(
                "/users/login",
                json={"username": "multipassuser", "password": old_pass}
            )
            assert old_login.status_code == 401
