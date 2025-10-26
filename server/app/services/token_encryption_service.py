"""
Token Encryption Service

Provides secure encryption/decryption of OAuth tokens using Fernet symmetric encryption.
Tokens are never exposed to the frontend and are encrypted at rest in the database.
"""

import json
from typing import Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64
import os

from app.core.exceptions import BadRequestException


class TokenEncryptionService:
    """
    Encrypts and decrypts OAuth tokens using Fernet symmetric encryption.

    Fernet guarantees that a message encrypted using it cannot be manipulated
    or read without the key. It uses AES in CBC mode with a 128-bit key for encryption.
    """

    def __init__(self, encryption_key: str):
        """
        Initialize encryption service with a key.

        Args:
            encryption_key: Base64-encoded Fernet key from environment variable

        Raises:
            ValueError: If encryption key is invalid or missing
        """
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required for token encryption")

        try:
            # Validate the key by attempting to create a Fernet instance
            self.cipher = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key format. Use Fernet.generate_key(): {e}")

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded Fernet key as string

        Usage:
            Run once to generate a key for your .env file:
            ```python
            from app.services.token_encryption_service import TokenEncryptionService
            print(TokenEncryptionService.generate_key())
            ```
        """
        return Fernet.generate_key().decode()

    def encrypt_tokens(self, token_data: Dict[str, Any]) -> str:
        """
        Encrypt OAuth token data for database storage.

        Args:
            token_data: Dictionary containing:
                - access_token: The OAuth access token
                - refresh_token: The OAuth refresh token
                - expires_at: Token expiration timestamp (ISO format or datetime)
                - token_type: Optional, usually "Bearer"
                - scope: Optional, granted scopes

        Returns:
            Encrypted token data as base64 string

        Raises:
            BadRequestException: If token_data is invalid
        """
        if not token_data or not isinstance(token_data, dict):
            raise BadRequestException("Token data must be a non-empty dictionary")

        required_fields = ["access_token", "refresh_token", "expires_at"]
        missing_fields = [field for field in required_fields if field not in token_data]
        if missing_fields:
            raise BadRequestException(f"Missing required token fields: {', '.join(missing_fields)}")

        # Convert datetime to ISO string if necessary
        if isinstance(token_data.get("expires_at"), datetime):
            token_data["expires_at"] = token_data["expires_at"].isoformat()

        try:
            # Serialize to JSON and encrypt
            json_data = json.dumps(token_data)
            encrypted = self.cipher.encrypt(json_data.encode())
            return encrypted.decode()
        except Exception as e:
            raise BadRequestException(f"Failed to encrypt token data: {e}")

    def decrypt_tokens(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt OAuth token data from database.

        Args:
            encrypted_data: Encrypted token string from database

        Returns:
            Dictionary containing decrypted token data:
                - access_token: The OAuth access token
                - refresh_token: The OAuth refresh token
                - expires_at: Token expiration as ISO string
                - token_type: Token type (usually "Bearer")
                - scope: Granted scopes

        Raises:
            BadRequestException: If decryption fails or data is corrupted
        """
        if not encrypted_data:
            raise BadRequestException("Encrypted data cannot be empty")

        try:
            # Decrypt and deserialize
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            token_data = json.loads(decrypted.decode())
            return token_data
        except Exception as e:
            raise BadRequestException(f"Failed to decrypt token data: {e}")

    def is_token_expired(self, token_data: Dict[str, Any], buffer_seconds: int = 300) -> bool:
        """
        Check if access token is expired or will expire soon.

        Args:
            token_data: Decrypted token data dictionary
            buffer_seconds: Consider token expired if expiring within this many seconds (default 5 min)

        Returns:
            True if token is expired or expiring soon, False otherwise
        """
        expires_at_str = token_data.get("expires_at")
        if not expires_at_str:
            return True  # No expiration info, assume expired

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            # Add buffer to prevent using tokens that are about to expire
            return datetime.now() >= (expires_at - timedelta(seconds=buffer_seconds))
        except Exception:
            return True  # Invalid expiration format, assume expired


# Singleton instance (initialized by FastAPI app)
_token_encryption_service: TokenEncryptionService | None = None


def get_token_encryption_service() -> TokenEncryptionService:
    """
    Get the global TokenEncryptionService instance.

    Returns:
        Configured TokenEncryptionService

    Raises:
        RuntimeError: If service hasn't been initialized
    """
    if _token_encryption_service is None:
        raise RuntimeError(
            "TokenEncryptionService not initialized. "
            "Call init_token_encryption_service() in app startup."
        )
    return _token_encryption_service


def init_token_encryption_service(encryption_key: str) -> None:
    """
    Initialize the global TokenEncryptionService instance.

    Should be called once during FastAPI application startup.

    Args:
        encryption_key: Fernet encryption key from settings
    """
    global _token_encryption_service
    _token_encryption_service = TokenEncryptionService(encryption_key)
