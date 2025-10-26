"""
Microsoft Graph API Integration Service

Handles OAuth token management and Microsoft Graph API calls for SharePoint/OneDrive access.
All API calls go through this service to ensure proper token refresh and error handling.
"""

import httpx
import secrets
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    PermissionDeniedException,
)
from app.models.provider_connection import ProviderConnection, ProviderType
from app.models.provider_config import ProviderConfig
from app.services.token_encryption_service import get_token_encryption_service


class MicrosoftGraphService:
    """
    Service for interacting with Microsoft Graph API.

    Handles OAuth flow, token refresh, and API requests to Microsoft Graph
    for SharePoint and OneDrive file access.
    """

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    OAUTH_AUTHORIZE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    OAUTH_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    # OAuth scopes for SharePoint/OneDrive access
    REQUIRED_SCOPES = [
        "Files.Read",
        "Files.Read.All",
        "Sites.Read.All",
        "offline_access",  # For refresh tokens
        "User.Read",  # To get user profile/tenant info
    ]

    def __init__(self, db: Session):
        """
        Initialize Graph service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.client_id = settings.sp_client_id
        self.client_secret = settings.sp_client_secret
        self.redirect_uri = settings.sp_redirect_uri

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError(
                "SharePoint provider not configured. Set SP_CLIENT_ID, "
                "SP_CLIENT_SECRET, and SP_REDIRECT_URI environment variables."
            )

    # ========================================================================
    # OAuth Flow
    # ========================================================================

    def generate_auth_url(self, state: str) -> str:
        """
        Generate Microsoft OAuth authorization URL.

        Args:
            state: CSRF protection state parameter

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": " ".join(self.REQUIRED_SCOPES),
            "state": state,
        }
        return f"{self.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self, code: str
    ) -> Tuple[Dict[str, Any], str]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Tuple of (token_data dict, tenant_id string)

        Raises:
            BadRequestException: If token exchange fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.OAUTH_TOKEN_URL, data=data)
                response.raise_for_status()
                token_response = response.json()
            except httpx.HTTPError as e:
                raise BadRequestException(f"Failed to exchange authorization code: {e}")

        # Extract token data
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)

        if not access_token or not refresh_token:
            raise BadRequestException("Invalid token response from Microsoft")

        # Calculate expiration time
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Get tenant ID from access token or user profile
        tenant_id = await self._get_tenant_id(access_token)

        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat(),
            "token_type": token_response.get("token_type", "Bearer"),
            "scope": token_response.get("scope", " ".join(self.REQUIRED_SCOPES)),
        }

        return token_data, tenant_id

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using refresh token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            Updated token data dictionary

        Raises:
            BadRequestException: If token refresh fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.OAUTH_TOKEN_URL, data=data)
                response.raise_for_status()
                token_response = response.json()
            except httpx.HTTPError as e:
                raise BadRequestException(f"Failed to refresh access token: {e}")

        access_token = token_response.get("access_token")
        new_refresh_token = token_response.get("refresh_token", refresh_token)
        expires_in = token_response.get("expires_in", 3600)

        if not access_token:
            raise BadRequestException("Invalid refresh token response")

        expires_at = datetime.now() + timedelta(seconds=expires_in)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_at": expires_at.isoformat(),
            "token_type": token_response.get("token_type", "Bearer"),
            "scope": token_response.get("scope", " ".join(self.REQUIRED_SCOPES)),
        }

    async def _get_tenant_id(self, access_token: str) -> str:
        """
        Get tenant ID from user profile.

        Args:
            access_token: Valid access token

        Returns:
            Microsoft 365 tenant ID

        Raises:
            BadRequestException: If unable to get tenant ID
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            try:
                # Get user's organization/tenant info
                response = await client.get(
                    f"{self.GRAPH_API_BASE}/me?$select=id,mail,userPrincipalName",
                    headers=headers,
                )
                response.raise_for_status()
                user_info = response.json()

                # Try to get tenant from organization endpoint
                org_response = await client.get(
                    f"{self.GRAPH_API_BASE}/organization",
                    headers=headers,
                )
                org_response.raise_for_status()
                org_data = org_response.json()

                if org_data.get("value"):
                    return org_data["value"][0].get("id", "common")

                # Fallback: extract from user principal name
                upn = user_info.get("userPrincipalName", "")
                if "@" in upn:
                    return upn.split("@")[1].replace(".", "-")

                return "common"
            except Exception as e:
                # Fallback to common if we can't determine tenant
                return "common"

    # ========================================================================
    # Token Management
    # ========================================================================

    async def get_valid_access_token(self, connection: ProviderConnection) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            connection: ProviderConnection with encrypted tokens

        Returns:
            Valid access token string

        Raises:
            BadRequestException: If token refresh fails
        """
        encryption_service = get_token_encryption_service()

        # Decrypt stored tokens
        token_data = encryption_service.decrypt_tokens(connection.encrypted_tokens)

        # Check if token is expired
        if encryption_service.is_token_expired(token_data):
            # Refresh the token
            refresh_token = token_data.get("refresh_token")
            if not refresh_token:
                raise BadRequestException("No refresh token available. Please re-authenticate.")

            # Get new tokens
            token_data = await self.refresh_access_token(refresh_token)

            # Update database with new tokens
            encrypted_tokens = encryption_service.encrypt_tokens(token_data)
            connection.encrypted_tokens = encrypted_tokens
            self.db.commit()

        return token_data["access_token"]

    # ========================================================================
    # Graph API Calls
    # ========================================================================

    async def _make_graph_request(
        self,
        connection: ProviderConnection,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Microsoft Graph API.

        Args:
            connection: ProviderConnection for authentication
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to graph base URL)
            params: Optional query parameters
            json_data: Optional JSON request body

        Returns:
            JSON response from API

        Raises:
            BadRequestException: If API call fails
        """
        access_token = await self.get_valid_access_token(connection)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        url = f"{self.GRAPH_API_BASE}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise NotFoundException(f"Resource not found: {endpoint}")
                elif e.response.status_code == 403:
                    raise PermissionDeniedException("Insufficient permissions to access resource")
                else:
                    error_detail = e.response.text
                    raise BadRequestException(f"Graph API error: {error_detail}")
            except httpx.HTTPError as e:
                raise BadRequestException(f"Failed to call Graph API: {e}")

    # ========================================================================
    # OneDrive Operations
    # ========================================================================

    async def get_onedrive_root(self, connection: ProviderConnection) -> Dict[str, Any]:
        """
        Get user's OneDrive root drive information.

        Returns:
            Drive metadata including ID, name, and type
        """
        return await self._make_graph_request(connection, "GET", "/me/drive")

    async def get_drive_children(
        self,
        connection: ProviderConnection,
        drive_id: str,
        item_id: str = "root",
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get children of a drive item (files and folders).

        Args:
            connection: ProviderConnection
            drive_id: Drive ID
            item_id: Item ID (default: "root")
            page_token: Optional pagination skiptoken

        Returns:
            Dict with 'value' (list of items) and optional '@odata.nextLink'
        """
        params = {}
        if page_token:
            params["$skiptoken"] = page_token

        endpoint = f"/drives/{drive_id}/items/{item_id}/children"
        return await self._make_graph_request(connection, "GET", endpoint, params=params)

    async def get_item_metadata(
        self,
        connection: ProviderConnection,
        drive_id: str,
        item_id: str,
    ) -> Dict[str, Any]:
        """
        Get metadata for a specific drive item.

        Returns:
            Item metadata including name, size, timestamps, etc.
        """
        endpoint = f"/drives/{drive_id}/items/{item_id}"
        return await self._make_graph_request(connection, "GET", endpoint)

    async def download_file(
        self,
        connection: ProviderConnection,
        drive_id: str,
        item_id: str,
    ) -> bytes:
        """
        Download file content from OneDrive/SharePoint.

        Args:
            connection: ProviderConnection
            drive_id: Drive ID
            item_id: Item ID

        Returns:
            File content as bytes

        Raises:
            BadRequestException: If download fails
        """
        access_token = await self.get_valid_access_token(connection)
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get download URL
        endpoint = f"/drives/{drive_id}/items/{item_id}/content"
        url = f"{self.GRAPH_API_BASE}/{endpoint}"

        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for large files
            try:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                return response.content
            except httpx.HTTPError as e:
                raise BadRequestException(f"Failed to download file: {e}")

    # ========================================================================
    # SharePoint Sites Operations
    # ========================================================================

    async def search_sites(
        self, connection: ProviderConnection, query: str
    ) -> Dict[str, Any]:
        """
        Search for SharePoint sites by name.

        Args:
            connection: ProviderConnection
            query: Search query string

        Returns:
            Dict with 'value' containing list of matching sites
        """
        params = {"search": query}
        return await self._make_graph_request(connection, "GET", "/sites", params=params)

    async def get_site_drives(
        self, connection: ProviderConnection, site_id: str
    ) -> Dict[str, Any]:
        """
        Get document libraries (drives) for a SharePoint site.

        Args:
            connection: ProviderConnection
            site_id: SharePoint site ID

        Returns:
            Dict with 'value' containing list of drives
        """
        endpoint = f"/sites/{site_id}/drives"
        return await self._make_graph_request(connection, "GET", endpoint)


def generate_state_token() -> str:
    """
    Generate a secure random state token for OAuth CSRF protection.

    Returns:
        URL-safe random string
    """
    return secrets.token_urlsafe(32)
