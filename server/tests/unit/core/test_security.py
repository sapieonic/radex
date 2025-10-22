"""
Unit tests for core security functions.
Tests password hashing, JWT token creation and validation.
"""
import pytest
from datetime import timedelta, datetime
from jose import jwt
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password(self):
        """Test password hashing creates valid hash"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Test verifying correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password fails"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that hashing same password produces different hashes (salting)"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        """Test hashing empty password"""
        password = ""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_special_characters_in_password(self):
        """Test password with special characters"""
        password = "p@ssw0rd!#$%^&*()"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and decoding"""

    def test_create_access_token(self):
        """Test creating access token"""
        data = {"sub": "testuser", "user_id": "123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots

    def test_create_token_with_custom_expiry(self):
        """Test creating token with custom expiration"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)

        # Decode and check expiration
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload

    def test_decode_valid_token(self):
        """Test decoding valid token"""
        data = {"sub": "testuser", "user_id": "123", "role": "user"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == "123"
        assert decoded["role"] == "user"
        assert "exp" in decoded

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None"""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_decode_malformed_token(self):
        """Test decoding malformed token"""
        malformed_tokens = [
            "",
            "abc",
            "a.b",
            "a.b.c.d",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # Only header
        ]

        for token in malformed_tokens:
            decoded = decode_access_token(token)
            assert decoded is None

    def test_decode_token_with_wrong_signature(self):
        """Test decoding token with wrong signature"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Tamper with the token by changing last character
        tampered_token = token[:-1] + ('A' if token[-1] != 'A' else 'B')

        decoded = decode_access_token(tampered_token)
        assert decoded is None

    def test_token_expiration_field(self):
        """Test that token contains expiration field"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)

        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded

        # Verify expiration is approximately 30 minutes from now
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + timedelta(minutes=30)

        # Allow 1 minute tolerance
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 60

    def test_token_default_expiration(self):
        """Test token uses default expiration from settings"""
        data = {"sub": "testuser"}
        token = create_access_token(data)  # No expires_delta

        decoded = decode_access_token(token)
        assert decoded is not None

        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)

        # Allow 1 minute tolerance
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 60

    def test_token_preserves_all_data(self):
        """Test that all data in payload is preserved"""
        data = {
            "sub": "testuser",
            "user_id": "123",
            "email": "test@example.com",
            "roles": ["user", "admin"],
            "is_active": True
        }
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == data["sub"]
        assert decoded["user_id"] == data["user_id"]
        assert decoded["email"] == data["email"]
        assert decoded["roles"] == data["roles"]
        assert decoded["is_active"] == data["is_active"]
