"""
Security utilities for authentication and authorization.

Provides JWT token generation/validation and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import hashlib

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    # Apply same pre-hashing as hash_password for long passwords
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')

    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password

    Note:
        Bcrypt has a 72-byte limit. Long passwords are pre-hashed with SHA256.
    """
    # Bcrypt has a 72-byte password limit
    # For long passwords, pre-hash with SHA256
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')

    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(
    subject: str,
    additional_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Token subject (typically user ID)
        additional_claims: Additional claims to include in token
        expires_delta: Token expiration time delta (None = use default)

    Returns:
        Encoded JWT token
    """
    settings = get_settings()

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.app.secret_key,
        algorithm=settings.jwt.algorithm,
    )

    return encoded_jwt


def create_refresh_token(
    subject: str,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: Token subject (typically user ID)
        additional_claims: Additional claims to include in token

    Returns:
        Encoded JWT token
    """
    settings = get_settings()

    expires_delta = timedelta(days=settings.jwt.refresh_token_expire_days)
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.app.secret_key,
        algorithm=settings.jwt.algorithm,
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.app.secret_key,
        algorithms=[settings.jwt.algorithm],
    )

    return payload


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify a JWT token and return the subject.

    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Token subject (user ID) if valid, None otherwise
    """
    try:
        payload = decode_token(token)

        # Verify token type
        if payload.get("type") != token_type:
            return None

        # Get subject
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            return None

        return subject

    except JWTError:
        return None


def encrypt_string(plaintext: str) -> str:
    """
    Encrypt a string for secure storage.

    Note: This is a placeholder for encryption. In production, use
    proper encryption libraries like cryptography.fernet.

    Args:
        plaintext: String to encrypt

    Returns:
        Encrypted string

    TODO: Implement proper encryption using cryptography library
    """
    # For now, just return the plaintext with a warning
    # In production, implement actual encryption
    import base64
    return base64.b64encode(plaintext.encode()).decode()


def decrypt_string(ciphertext: str) -> str:
    """
    Decrypt an encrypted string.

    Note: This is a placeholder for decryption. In production, use
    proper encryption libraries like cryptography.fernet.

    Args:
        ciphertext: Encrypted string

    Returns:
        Decrypted string

    TODO: Implement proper decryption using cryptography library
    """
    # For now, just decode the base64
    # In production, implement actual decryption
    import base64
    return base64.b64decode(ciphertext.encode()).decode()
