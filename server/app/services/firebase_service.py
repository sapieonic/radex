"""
Firebase Authentication Service

This service handles Firebase Admin SDK initialization and token verification.
It provides functionality to verify Firebase ID tokens and extract user information.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.exceptions import FirebaseError

from app.config import settings
from app.models.user import AuthProvider

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for Firebase authentication operations"""

    _initialized = False
    _app = None

    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK with service account credentials"""
        if cls._initialized:
            return

        # Check if Firebase credentials are provided
        if not settings.firebase_admin_sdk_json:
            logger.warning("Firebase Admin SDK credentials not provided - Firebase authentication will not be available")
            raise ValueError("Firebase credentials not configured")

        try:
            # Parse Firebase service account JSON from environment variable
            service_account_info = json.loads(settings.firebase_admin_sdk_json)

            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(service_account_info)
            cls._app = firebase_admin.initialize_app(cred)
            cls._initialized = True

            logger.info("Firebase Admin SDK initialized successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Firebase service account JSON: {e}")
            raise ValueError("Invalid Firebase service account JSON format")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise

    @classmethod
    def verify_id_token(cls, id_token: str, check_revoked: bool = True) -> Dict[str, Any]:
        """
        Verify a Firebase ID token and return decoded token

        Args:
            id_token: Firebase ID token from the client
            check_revoked: Whether to check if the token has been revoked

        Returns:
            Dict containing decoded token information

        Raises:
            ValueError: If token is invalid or expired
            FirebaseError: If there's an error verifying the token
        """
        if not cls._initialized:
            cls.initialize()

        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token, check_revoked=check_revoked)

            logger.info(f"Successfully verified token for user: {decoded_token.get('uid')}")
            return decoded_token

        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid ID token: {e}")
            raise ValueError("Invalid authentication token")
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired ID token: {e}")
            raise ValueError("Authentication token has expired")
        except auth.RevokedIdTokenError as e:
            logger.warning(f"Revoked ID token: {e}")
            raise ValueError("Authentication token has been revoked")
        except FirebaseError as e:
            logger.error(f"Firebase error verifying token: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            raise ValueError("Failed to verify authentication token")

    @classmethod
    def get_user_info(cls, uid: str) -> Dict[str, Any]:
        """
        Get user information from Firebase by UID

        Args:
            uid: Firebase user UID

        Returns:
            Dict containing user information

        Raises:
            ValueError: If user not found
            FirebaseError: If there's an error fetching user info
        """
        if not cls._initialized:
            cls.initialize()

        try:
            user_record = auth.get_user(uid)

            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "email_verified": user_record.email_verified,
                "display_name": user_record.display_name,
                "photo_url": user_record.photo_url,
                "disabled": user_record.disabled,
                "provider_data": user_record.provider_data,
            }

        except auth.UserNotFoundError as e:
            logger.warning(f"User not found: {uid}")
            raise ValueError(f"User not found: {uid}")
        except FirebaseError as e:
            logger.error(f"Firebase error fetching user info: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user info: {e}")
            raise ValueError("Failed to fetch user information")

    @classmethod
    def extract_auth_provider(cls, decoded_token: Dict[str, Any]) -> AuthProvider:
        """
        Extract the authentication provider from decoded token

        Args:
            decoded_token: Decoded Firebase ID token

        Returns:
            AuthProvider enum value
        """
        firebase_providers = decoded_token.get("firebase", {}).get("sign_in_provider", "")

        # Map Firebase provider identifiers to our AuthProvider enum
        provider_mapping = {
            "google.com": AuthProvider.GOOGLE,
            "microsoft.com": AuthProvider.MICROSOFT,
            "oidc.okta": AuthProvider.OKTA,
            "saml.okta": AuthProvider.OKTA,
            "password": AuthProvider.PASSWORD,
        }

        # Check provider_data for more detailed provider information
        provider_data = decoded_token.get("firebase", {}).get("identities", {})

        # First, check exact match in provider mapping
        if firebase_providers in provider_mapping:
            return provider_mapping[firebase_providers]

        # Try to match based on provider string contains
        firebase_providers_lower = firebase_providers.lower()
        if "google" in firebase_providers_lower:
            return AuthProvider.GOOGLE
        elif "microsoft" in firebase_providers_lower:
            return AuthProvider.MICROSOFT
        elif "okta" in firebase_providers_lower or "oidc.okta" in firebase_providers_lower:
            return AuthProvider.OKTA

        # Check identities in provider_data
        if provider_data:
            if "google.com" in provider_data:
                return AuthProvider.GOOGLE
            elif "microsoft.com" in provider_data:
                return AuthProvider.MICROSOFT
            elif any("okta" in str(k).lower() for k in provider_data.keys()):
                return AuthProvider.OKTA
            elif "oidc.okta" in provider_data:
                return AuthProvider.OKTA

        # Default to password if can't determine
        logger.warning(f"Could not determine provider from token, defaulting to PASSWORD. Provider: {firebase_providers}, Identities: {provider_data}")
        return AuthProvider.PASSWORD

    @classmethod
    def set_custom_user_claims(cls, uid: str, custom_claims: Dict[str, Any]):
        """
        Set custom claims for a user (e.g., roles, permissions)

        Args:
            uid: Firebase user UID
            custom_claims: Dictionary of custom claims to set

        Raises:
            FirebaseError: If there's an error setting custom claims
        """
        if not cls._initialized:
            cls.initialize()

        try:
            auth.set_custom_user_claims(uid, custom_claims)
            logger.info(f"Successfully set custom claims for user: {uid}")

        except FirebaseError as e:
            logger.error(f"Firebase error setting custom claims: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error setting custom claims: {e}")
            raise

    @classmethod
    def revoke_refresh_tokens(cls, uid: str):
        """
        Revoke all refresh tokens for a user

        Args:
            uid: Firebase user UID

        Raises:
            FirebaseError: If there's an error revoking tokens
        """
        if not cls._initialized:
            cls.initialize()

        try:
            auth.revoke_refresh_tokens(uid)
            logger.info(f"Successfully revoked refresh tokens for user: {uid}")

        except FirebaseError as e:
            logger.error(f"Firebase error revoking refresh tokens: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error revoking refresh tokens: {e}")
            raise

    @classmethod
    def delete_user(cls, uid: str):
        """
        Delete a user from Firebase

        Args:
            uid: Firebase user UID

        Raises:
            FirebaseError: If there's an error deleting user
        """
        if not cls._initialized:
            cls.initialize()

        try:
            auth.delete_user(uid)
            logger.info(f"Successfully deleted Firebase user: {uid}")

        except FirebaseError as e:
            logger.error(f"Firebase error deleting user: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting user: {e}")
            raise


# Initialize Firebase on module import (optional - will initialize on first use if not done here)
try:
    FirebaseService.initialize()
except Exception as e:
    logger.warning(f"Firebase Admin SDK not initialized on import (will attempt on first use): {e}")
    # This is not a critical error - Firebase initialization can happen lazily
    # The app will still work with legacy JWT authentication
