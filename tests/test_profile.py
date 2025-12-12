"""
Unit tests for user profile management logic.
"""

import pytest
from pydantic import ValidationError

from app.schemas import UserProfileUpdate, PasswordChangeRequest


class TestUserProfileUpdateSchema:
    """Test UserProfileUpdate schema validation."""

    def test_valid_username_only(self):
        """Test updating username only."""
        profile = UserProfileUpdate(username="newuser")
        assert profile.username == "newuser"
        assert profile.email is None

    def test_valid_email_only(self):
        """Test updating email only."""
        profile = UserProfileUpdate(email="newemail@example.com")
        assert profile.email == "newemail@example.com"
        assert profile.username is None

    def test_valid_both_fields(self):
        """Test updating both username and email."""
        profile = UserProfileUpdate(username="newuser", email="newemail@example.com")
        assert profile.username == "newuser"
        assert profile.email == "newemail@example.com"

    def test_empty_update(self):
        """Test creating update with no fields (should be valid)."""
        profile = UserProfileUpdate()
        assert profile.username is None
        assert profile.email is None

    def test_invalid_email_format(self):
        """Test that invalid email format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(email="not-an-email")
        assert "email" in str(exc_info.value).lower()

    def test_empty_string_username(self):
        """Test that empty string username is rejected (min_length=3)."""
        with pytest.raises(ValidationError) as exc_info:
            UserProfileUpdate(username="")
        assert "username" in str(exc_info.value).lower()

    def test_empty_string_email(self):
        """Test that empty string email is validated."""
        with pytest.raises(ValidationError):
            UserProfileUpdate(email="")


class TestPasswordChangeRequestSchema:
    """Test PasswordChangeRequest schema validation."""

    def test_valid_password_change(self):
        """Test valid password change request."""
        request = PasswordChangeRequest(
            current_password="OldPass123!",
            new_password="NewPass456@"
        )
        assert request.current_password == "OldPass123!"
        assert request.new_password == "NewPass456@"

    def test_password_same_as_current(self):
        """Test that new password same as current is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                current_password="SamePass123!",
                new_password="SamePass123!"
            )
        error_msg = str(exc_info.value).lower()
        assert "different" in error_msg or "same" in error_msg

    def test_missing_current_password(self):
        """Test that missing current password is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(new_password="NewPass123!")
        assert "current_password" in str(exc_info.value).lower()

    def test_missing_new_password(self):
        """Test that missing new password is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(current_password="OldPass123!")
        assert "new_password" in str(exc_info.value).lower()

    def test_weak_new_password_no_uppercase(self):
        """Test that password is accepted (no uppercase requirement in schema)."""
        # Note: Schema only validates min_length=6, not password complexity
        request = PasswordChangeRequest(
            current_password="oldpass123!",
            new_password="newpass123!"
        )
        assert request.new_password == "newpass123!"

    def test_weak_new_password_no_lowercase(self):
        """Test that password is accepted (no lowercase requirement in schema)."""
        request = PasswordChangeRequest(
            current_password="OLDPASS123!",
            new_password="NEWPASS123!"
        )
        assert request.new_password == "NEWPASS123!"

    def test_weak_new_password_no_digit(self):
        """Test that password is accepted (no digit requirement in schema)."""
        request = PasswordChangeRequest(
            current_password="OldPass!",
            new_password="NewPass!"
        )
        assert request.new_password == "NewPass!"

    def test_weak_new_password_no_special(self):
        """Test that password is accepted (no special char requirement in schema)."""
        request = PasswordChangeRequest(
            current_password="OldPass123",
            new_password="NewPass123"
        )
        assert request.new_password == "NewPass123"

    def test_weak_new_password_too_short(self):
        """Test that password shorter than 6 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(
                current_password="OldPass123!",
                new_password="Short"
            )
        error_msg = str(exc_info.value).lower()
        assert "password" in error_msg or "6" in str(exc_info.value)

    def test_strong_passwords_different(self):
        """Test that two different strong passwords are accepted."""
        request = PasswordChangeRequest(
            current_password="ValidOld123!",
            new_password="ValidNew456@"
        )
        assert request.current_password == "ValidOld123!"
        assert request.new_password == "ValidNew456@"

    def test_empty_current_password(self):
        """Test that empty current password is rejected."""
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="",
                new_password="NewPass123!"
            )

    def test_empty_new_password(self):
        """Test that empty new password is rejected."""
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="OldPass123!",
                new_password=""
            )

    def test_whitespace_only_passwords(self):
        """Test that whitespace-only passwords are rejected."""
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="   ",
                new_password="NewPass123!"
            )
