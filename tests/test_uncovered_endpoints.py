"""
Tests for uncovered endpoints and error conditions in main.py
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, schemas
from app.security import hash_password, create_access_token
import uuid


TEST_DATABASE_URL = "sqlite:///./test_coverage.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
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


def create_test_user(username=None, email=None, role="user"):
    """Helper to create a test user."""
    if username is None:
        unique = str(uuid.uuid4())[:8]
        username = f"testuser_{unique}"
        email = f"test_{unique}@example.com"
    
    db = TestingSessionLocal()
    user = models.User(
        username=username,
        email=email,
        password_hash=hash_password("password123"),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def test_get_current_user_invalid_token():
    """Test get_current_user with invalid token."""
    response = client.get(
        "/calculations",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401
    assert "Invalid authentication credentials" in response.json()["detail"]


def test_get_current_user_no_subject():
    """Test get_current_user when token has no subject."""
    # Create a token without 'sub' field
    import jwt
    from app.security import SECRET_KEY, ALGORITHM
    from datetime import datetime, timedelta, timezone
    
    token_data = {
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc)
        # Missing "sub" field
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    response = client.get(
        "/calculations",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_get_current_user_user_not_found():
    """Test get_current_user when user doesn't exist in database."""
    # Create token for non-existent user
    token = create_access_token(subject="nonexistent_user")
    
    response = client.get(
        "/calculations",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert "User not found" in response.json()["detail"]


def test_require_role_insufficient_privileges():
    """Test require_role decorator with insufficient privileges."""
    # Create regular user
    user = create_test_user(role="user")
    token = create_access_token(subject=user.username)
    
    # Try to access admin endpoint
    response = client.get(
        "/admin/tokens",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Insufficient privileges" in response.json()["detail"]


def test_revoke_my_token_by_string_not_found():
    """Test /users/me/revoke when token not found."""
    user = create_test_user()
    token = create_access_token(subject=user.username)
    
    # Try to revoke non-existent refresh token
    response = client.post(
        "/users/me/revoke",
        json={"refresh_token": "non.existent.token"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    assert "refresh token not found" in response.json()["detail"]


def test_revoke_my_token_by_string_success():
    """Test successful token revocation via /users/me/revoke."""
    # Create user
    user = create_test_user()
    
    # Login to get refresh token
    login_response = client.post(
        "/users/login",
        json={"username": user.username, "password": "password123"}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # Revoke the refresh token
    revoke_response = client.post(
        "/users/me/revoke",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["msg"] == "revoked"
    
    # Try to use revoked token
    refresh_response = client.post(
        "/users/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 401


def test_admin_endpoints_with_admin_user():
    """Test admin endpoints with admin user."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Test admin/tokens endpoint
    response = client.get(
        "/admin/tokens",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Test admin/users endpoint
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200


def test_list_users_endpoint():
    """Test /users/ endpoint (admin only)."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Create some regular users
    create_test_user(username="user1", email="user1@test.com")
    create_test_user(username="user2", email="user2@test.com")
    
    # List users
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3  # admin + 2 regular users


def test_set_user_role():
    """Test /users/{username}/role endpoint."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Create regular user
    user = create_test_user(username="testuser", email="test@test.com", role="user")
    
    # Change user role
    response = client.post(
        f"/users/{user.username}/role",
        json={"role": "moderator"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "moderator"


def test_set_user_role_user_not_found():
    """Test /users/{username}/role with non-existent user."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Try to change role of non-existent user
    response = client.post(
        "/users/nonexistent/role",
        json={"role": "moderator"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_revoke_all_for_user():
    """Test /users/{username}/revoke_all endpoint."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Create regular user and login
    user = create_test_user(username="testuser", email="test@test.com")
    login_response = client.post(
        "/users/login",
        json={"username": user.username, "password": "password123"}
    )
    
    # Revoke all tokens for user
    response = client.post(
        f"/users/{user.username}/revoke_all",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "revoked all"


def test_revoke_all_for_nonexistent_user():
    """Test /users/{username}/revoke_all with non-existent user."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Try to revoke tokens for non-existent user
    response = client.post(
        "/users/nonexistent/revoke_all",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_admin_list_tokens_for_user():
    """Test /admin/users/{username}/tokens endpoint."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Create user and login to generate tokens
    user = create_test_user(username="testuser", email="test@test.com")
    client.post(
        "/users/login",
        json={"username": user.username, "password": "password123"}
    )
    
    # List tokens for user
    response = client.get(
        f"/admin/users/{user.username}/tokens",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    tokens = response.json()
    assert len(tokens) > 0


def test_admin_list_tokens_for_nonexistent_user():
    """Test /admin/users/{username}/tokens with non-existent user."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Try to list tokens for non-existent user
    response = client.get(
        "/admin/users/nonexistent/tokens",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_admin_revoke_by_token():
    """Test /admin/tokens/revoke endpoint."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Create user and login
    user = create_test_user()
    login_response = client.post(
        "/users/login",
        json={"username": user.username, "password": "password123"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Admin revokes the token
    response = client.post(
        "/admin/tokens/revoke",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "revoked"


def test_admin_revoke_nonexistent_token():
    """Test /admin/tokens/revoke with non-existent token."""
    # Create admin user
    admin_user = create_test_user(username="admin", email="admin@test.com", role="admin")
    admin_token = create_access_token(subject=admin_user.username)
    
    # Try to revoke non-existent token
    response = client.post(
        "/admin/tokens/revoke",
        json={"refresh_token": "non.existent.token"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert "Token not found" in response.json()["detail"]


def test_calculation_read_not_found():
    """Test reading non-existent calculation."""
    user = create_test_user()
    token = create_access_token(subject=user.username)
    
    response = client.get(
        "/calculations/99999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    assert "Calculation not found" in response.json()["detail"]


def test_calculation_update_not_found():
    """Test updating non-existent calculation."""
    user = create_test_user()
    token = create_access_token(subject=user.username)
    
    response = client.put(
        "/calculations/99999",
        json={"a": 10, "b": 5, "type": "Add"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_calculation_patch_not_found():
    """Test patching non-existent calculation."""
    user = create_test_user()
    token = create_access_token(subject=user.username)
    
    response = client.patch(
        "/calculations/99999",
        json={"a": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_calculation_delete_not_found():
    """Test deleting non-existent calculation."""
    user = create_test_user()
    token = create_access_token(subject=user.username)
    
    response = client.delete(
        "/calculations/99999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_calculation_patch_success():
    """Test successful PATCH of calculation."""
    user = create_test_user()
    token = create_access_token(subject=user.username)
    
    # Create calculation
    create_response = client.post(
        "/calculations",
        json={"a": 10, "b": 5, "type": "Add"},
        headers={"Authorization": f"Bearer {token}"}
    )
    calc_id = create_response.json()["id"]
    
    # Patch only b
    patch_response = client.patch(
        f"/calculations/{calc_id}",
        json={"b": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["a"] == 10  # unchanged
    assert updated["b"] == 10  # changed
    assert updated["result"] == 20  # recomputed


def test_user_login_missing_credentials():
    """Test login without username or email."""
    response = client.post(
        "/users/login",
        json={"password": "password123"}
    )
    assert response.status_code == 400
    assert "username or email required" in response.json()["detail"]


def test_refresh_token_missing():
    """Test refresh without token."""
    response = client.post(
        "/users/refresh",
        json={"refresh_token": ""}
    )
    assert response.status_code == 400


def test_logout_missing_token():
    """Test logout without refresh token."""
    user = create_test_user()
    token = create_access_token(subject=user.username)
    
    response = client.post(
        "/users/logout",
        json={"refresh_token": ""},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
