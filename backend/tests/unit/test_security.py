"""
Unit tests for security utilities.

Tests password hashing, JWT token creation/validation, and encryption.
"""

import time
from datetime import timedelta

import pytest
from jose import JWTError, jwt

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_string,
    encrypt_string,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test that passwords are hashed correctly."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test failed password verification with wrong password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that same password generates different hashes."""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different salts should produce different hashes
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestAccessToken:
    """Test JWT access token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        user_id = "user-123-456"
        token = create_access_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test decoding access token."""
        user_id = "user-123-456"
        token = create_access_token(subject=user_id)

        payload = decode_token(token)

        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_access_token(self):
        """Test verifying access token."""
        user_id = "user-123-456"
        token = create_access_token(subject=user_id)

        subject = verify_token(token, token_type="access")

        assert subject == user_id

    def test_access_token_with_additional_claims(self):
        """Test access token with additional claims."""
        user_id = "user-123-456"
        additional_claims = {"role": "admin", "email": "admin@example.com"}

        token = create_access_token(
            subject=user_id, additional_claims=additional_claims
        )
        payload = decode_token(token)

        assert payload["sub"] == user_id
        assert payload["role"] == "admin"
        assert payload["email"] == "admin@example.com"

    def test_access_token_custom_expiration(self):
        """Test access token with custom expiration."""
        user_id = "user-123-456"
        expires_delta = timedelta(minutes=60)

        token = create_access_token(subject=user_id, expires_delta=expires_delta)
        payload = decode_token(token)

        # Check expiration is roughly 60 minutes from now
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        difference = exp_timestamp - iat_timestamp

        # Should be 3600 seconds (60 minutes)
        assert 3595 <= difference <= 3605  # Allow 5 second margin

    def test_expired_access_token(self):
        """Test that expired tokens are rejected."""
        user_id = "user-123-456"
        # Create token that expires immediately
        token = create_access_token(
            subject=user_id, expires_delta=timedelta(seconds=-1)
        )

        # Token should be invalid
        subject = verify_token(token, token_type="access")
        assert subject is None

    def test_invalid_token_signature(self):
        """Test that tokens with invalid signatures are rejected."""
        user_id = "user-123-456"
        token = create_access_token(subject=user_id)

        # Tamper with the token
        parts = token.split(".")
        if len(parts) == 3:
            # Change the signature
            tampered_token = f"{parts[0]}.{parts[1]}.invalid_signature"

            subject = verify_token(tampered_token, token_type="access")
            assert subject is None

    def test_malformed_token(self):
        """Test that malformed tokens are rejected."""
        subject = verify_token("not.a.valid.token", token_type="access")
        assert subject is None


class TestRefreshToken:
    """Test JWT refresh token creation and validation."""

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "user-123-456"
        token = create_refresh_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_refresh_token(self):
        """Test decoding refresh token."""
        user_id = "user-123-456"
        token = create_refresh_token(subject=user_id)

        payload = decode_token(token)

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_verify_refresh_token(self):
        """Test verifying refresh token."""
        user_id = "user-123-456"
        token = create_refresh_token(subject=user_id)

        subject = verify_token(token, token_type="refresh")

        assert subject == user_id

    def test_refresh_token_with_additional_claims(self):
        """Test refresh token with additional claims."""
        user_id = "user-123-456"
        additional_claims = {"device": "mobile"}

        token = create_refresh_token(
            subject=user_id, additional_claims=additional_claims
        )
        payload = decode_token(token)

        assert payload["sub"] == user_id
        assert payload["device"] == "mobile"

    def test_wrong_token_type(self):
        """Test that access token is rejected when refresh token expected."""
        user_id = "user-123-456"
        access_token = create_access_token(subject=user_id)

        # Try to verify as refresh token
        subject = verify_token(access_token, token_type="refresh")
        assert subject is None

    def test_refresh_token_wrong_type(self):
        """Test that refresh token is rejected when access token expected."""
        user_id = "user-123-456"
        refresh_token = create_refresh_token(subject=user_id)

        # Try to verify as access token
        subject = verify_token(refresh_token, token_type="access")
        assert subject is None


class TestEncryption:
    """Test string encryption and decryption."""

    def test_encrypt_string(self):
        """Test string encryption."""
        plaintext = "sensitive_token_12345"
        ciphertext = encrypt_string(plaintext)

        assert ciphertext != plaintext
        assert len(ciphertext) > 0

    def test_decrypt_string(self):
        """Test string decryption."""
        plaintext = "sensitive_token_12345"
        ciphertext = encrypt_string(plaintext)
        decrypted = decrypt_string(ciphertext)

        assert decrypted == plaintext

    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption/decryption roundtrip with various strings."""
        test_strings = [
            "simple",
            "with spaces",
            "with-special-chars!@#$%",
            "unicode-café",
            "a" * 1000,  # Long string
        ]

        for original in test_strings:
            encrypted = encrypt_string(original)
            decrypted = decrypt_string(encrypted)
            assert decrypted == original

    def test_empty_string_encryption(self):
        """Test encryption of empty string."""
        plaintext = ""
        ciphertext = encrypt_string(plaintext)
        decrypted = decrypt_string(ciphertext)

        assert decrypted == plaintext


class TestTokenEdgeCases:
    """Test edge cases for token handling."""

    def test_token_without_subject(self):
        """Test token without subject claim."""
        from app.config import get_settings

        settings = get_settings()

        # Create token without 'sub' claim
        payload = {"type": "access", "exp": time.time() + 3600}
        token = jwt.encode(payload, settings.app.secret_key, algorithm="HS256")

        subject = verify_token(token, token_type="access")
        assert subject is None

    def test_token_with_null_subject(self):
        """Test token with null subject claim."""
        from app.config import get_settings

        settings = get_settings()

        # Create token with null 'sub' claim
        payload = {"sub": None, "type": "access", "exp": time.time() + 3600}
        token = jwt.encode(payload, settings.app.secret_key, algorithm="HS256")

        subject = verify_token(token, token_type="access")
        assert subject is None

    def test_empty_token(self):
        """Test empty token string."""
        subject = verify_token("", token_type="access")
        assert subject is None
