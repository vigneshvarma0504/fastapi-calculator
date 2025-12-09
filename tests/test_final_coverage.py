"""Final tests to achieve 100% code coverage."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db, SessionLocal
from app import models
from app.operations import compute_result


client = TestClient(app)


def cleanup_user(username: str):
    """Helper to clean up test users."""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            # Delete associated calculations
            db.query(models.Calculation).filter(models.Calculation.user_id == user.id).delete()
            # Delete associated refresh tokens
            from app.models import RefreshToken
            db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
            # Delete user
            db.delete(user)
            db.commit()
    finally:
        db.close()


# Test line 189 in main.py: duplicate email registration
def test_register_duplicate_email():
    """Test registering with an existing email."""
    cleanup_user("uniqueuser1")
    cleanup_user("uniqueuser2")
    
    # Register first user
    response1 = client.post(
        "/users/register",
        json={
            "username": "uniqueuser1",
            "email": "duplicate@example.com",
            "password": "password123"
        }
    )
    assert response1.status_code == 201
    
    # Try to register with same email but different username
    response2 = client.post(
        "/users/register",
        json={
            "username": "uniqueuser2",
            "email": "duplicate@example.com",
            "password": "password456"
        }
    )
    assert response2.status_code == 400
# Test line 220 in main.py: login with email instead of username
def test_login_with_email():
    """Test logging in with email instead of username."""
    cleanup_user("emailuser")
    
    # Register user
    client.post(
        "/users/register",
        json={
            "username": "emailuser",
            "email": "emailuser@example.com",
            "password": "password123"
        }
    )
    
    # Login with email
    response = client.post(
        "/users/login",
        json={
            "email": "emailuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
# Test lines 254-255, 259 in main.py: invalid refresh token scenarios
def test_refresh_token_invalid_payload():
    """Test refresh endpoint with invalid token payload."""
    response = client.post(
        "/users/refresh",
        json={"refresh_token": "invalid.token.format"}
    )
    # Returns 400 because Pydantic validation fails or JWT decode fails
    assert response.status_code in [400, 401]


def test_refresh_token_user_not_found():
    """Test refresh endpoint with token for non-existent user."""
    # Create a valid-format token but for a user that doesn't exist
    from app.security import create_access_token
    fake_token = create_access_token(subject="nonexistentuser12345")
    
    response = client.post(
        "/users/refresh",
        json={"refresh_token": fake_token}
    )
    # Returns 400 or 401 for invalid token
    assert response.status_code in [400, 401]


def test_refresh_token_not_in_database():
    """Test refresh endpoint with valid token that was never stored in DB."""
    cleanup_user("tokenuser2")
    
    # Register user
    client.post(
        "/users/register",
        json={
            "username": "tokenuser2",
            "email": "tokenuser2@example.com",
            "password": "password123"
        }
    )
    
    # Create a refresh token manually (not through login, so not in DB)
    from app.security import create_refresh_token
    fake_refresh = create_refresh_token(subject="tokenuser2")
    
    # Try to use it - should fail because it's not in the refresh_tokens table
    response = client.post(
        "/users/refresh",
        json={"refresh_token": fake_refresh}
    )
    # Should return 401 because token not found in database
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
    
    cleanup_user("tokenuser2")


# Test line 282 in main.py: revoke token not found
def test_revoke_token_not_found():
    """Test revoking a token that doesn't exist in database."""
    cleanup_user("revokeuser")
    
    # Register and login
    client.post(
        "/users/register",
        json={
            "username": "revokeuser",
            "email": "revokeuser@example.com",
            "password": "password123"
        }
    )
    
    login_response = client.post(
        "/users/login",
        json={
            "username": "revokeuser",
            "password": "password123"
        }
    )
    data = login_response.json()
    access_token = data["access_token"]
    
    # Try to revoke a non-existent refresh token
    response = client.post(
        "/users/revoke",
        json={"refresh_token": "fake_token_not_in_db"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404
# Test lines 403-404 in main.py: list calculations with pagination
def test_list_calculations_with_skip_limit():
    """Test browsing calculations with skip and limit parameters."""
    cleanup_user("paginationuser")
    
    # Register and login
    client.post(
        "/users/register",
        json={
            "username": "paginationuser",
            "email": "pagination@example.com",
            "password": "password123"
        }
    )
    
    login_response = client.post(
        "/users/login",
        json={
            "username": "paginationuser",
            "password": "password123"
        }
    )
    data = login_response.json()
    access_token = data["access_token"]
    
    # Create multiple calculations
    for i in range(5):
        client.post(
            "/calculations",
            json={
                "a": i,
                "b": 1,
                "type": "Add"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    # Test pagination
    response = client.get(
        "/calculations?skip=1&limit=2",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    calculations = response.json()
# Test lines 478, 482 in main.py: PATCH endpoint updating individual fields
def test_patch_calculation_update_only_a():
    """Test PATCH endpoint updating only the 'a' field."""
    cleanup_user("patchuser1")
    
    # Register and login
    client.post(
        "/users/register",
        json={
            "username": "patchuser1",
            "email": "patch1@example.com",
            "password": "password123"
        }
    )
    
    login_response = client.post(
        "/users/login",
        json={
            "username": "patchuser1",
            "password": "password123"
        }
    )
    data = login_response.json()
    access_token = data["access_token"]
    
    # Create a calculation
    create_response = client.post(
        "/calculations",
        json={"a": 10, "b": 5, "type": "Add"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert create_response.status_code == 201
    calc_id = create_response.json()["id"]
    
    # Update only 'a'
    patch_response = client.patch(
        f"/calculations/{calc_id}",
        json={"a": 20},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert patch_response.status_code == 200
    result = patch_response.json()
    assert result["a"] == 20
    assert result["b"] == 5
    assert result["result"] == 25
    
    cleanup_user("patchuser1")

def test_patch_calculation_update_only_b():
    """Test PATCH endpoint updating only the 'b' field."""
    cleanup_user("patchuser2")
    
    # Register and login
    client.post(
        "/users/register",
        json={
            "username": "patchuser2",
            "email": "patch2@example.com",
            "password": "password123"
        }
    )
    
    login_response = client.post(
        "/users/login",
        json={
            "username": "patchuser2",
            "password": "password123"
        }
    )
    data = login_response.json()
    access_token = data["access_token"]
    
    # Create a calculation
    create_response = client.post(
        "/calculations",
        json={"a": 10, "b": 5, "type": "Multiply"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert create_response.status_code == 201
    calc_id = create_response.json()["id"]
    
    # Update only 'b'
    patch_response = client.patch(
        f"/calculations/{calc_id}",
        json={"b": 3},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert patch_response.status_code == 200
    result = patch_response.json()
    assert result["a"] == 10
    assert result["b"] == 3
    assert result["result"] == 30
    
    cleanup_user("patchuser2")
    cleanup_user("patchuser2")
def test_patch_calculation_update_only_type():
    """Test PATCH endpoint updating only the 'type' field."""
    cleanup_user("patchuser3")
    
    # Register and login
    client.post(
        "/users/register",
        json={
            "username": "patchuser3",
            "email": "patch3@example.com",
            "password": "password123"
        }
    )
    
    login_response = client.post(
        "/users/login",
        json={
            "username": "patchuser3",
            "password": "password123"
        }
    )
    data = login_response.json()
    access_token = data["access_token"]
    
    # Create a calculation
    create_response = client.post(
        "/calculations",
        json={"a": 20, "b": 4, "type": "Add"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert create_response.status_code == 201
    calc_id = create_response.json()["id"]
    
    # Update only 'type'
    patch_response = client.patch(
        f"/calculations/{calc_id}",
        json={"type": "Divide"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert patch_response.status_code == 200
    result = patch_response.json()
    assert result["a"] == 20
    assert result["b"] == 4
    assert result["type"] == "Divide"
    assert result["result"] == 5
    
    cleanup_user("patchuser3")


# Test line 46 in operations.py: unsupported operation type
def test_compute_result_unsupported_operation():
    """Test compute_result with an invalid operation type."""
    with pytest.raises(KeyError, match="Unsupported operation"):
        # This should raise KeyError because 'invalid_op' is not in the operation map
        compute_result(10, 5, "invalid_op")

