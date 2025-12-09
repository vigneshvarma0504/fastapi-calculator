import pytest
from pydantic import ValidationError
from app.schemas import UserCreate

def test_usercreate_valid():
    user = UserCreate(username="testuser", email="test@example.com", password="securepass")
    assert user.username == "testuser"

def test_usercreate_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(username="testuser", email="not-an-email", password="securepass")

def test_usercreate_short_password():
    with pytest.raises(ValidationError):
        UserCreate(username="testuser", email="test@example.com", password="123")
