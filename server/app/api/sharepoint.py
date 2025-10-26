"""
SharePoint/OneDrive Provider API Endpoints

Implements OAuth flow, file browsing, and sync functionality for Microsoft 365 integration.
All endpoints require user authentication. No tokens or secrets are exposed to the frontend.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import secrets

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.provider_connection import ProviderConnection, ProviderType
from app.models.provider_config import ProviderConfig
from app.models.provider_item_ref import ProviderItemRef
from app.schemas.sharepoint import (
    SharePointAuthStartResponse,
    SharePointAuthCallbackRequest,
    SharePointAuthCallbackResponse,
    ProviderConnectionInfo,
    ProviderConnectionsResponse,
    DriveItemsResponse,
    DriveItem,
    DriveItemType,
    DrivesResponse,
    DriveInfo,
    SitesResponse,
    SiteInfo,
)
from app.services.microsoft_graph_service import MicrosoftGraphService, generate_state_token
from app.services.token_encryption_service import get_token_encryption_service
from app.core.exceptions import BadRequestException, NotFoundException
from app.config import settings

router = APIRouter(
    prefix="/providers/sharepoint",
    tags=["SharePoint Provider"],
)

# In-memory state storage (in production, use Redis with TTL)
# Maps state -> user_id for OAuth CSRF protection
_oauth_states: dict[str, UUID] = {}


def check_sharepoint_enabled():
    """
    Dependency to check if SharePoint provider is enabled.

    Raises:
        HTTPException: If SharePoint provider is not enabled
    """
    if not settings.enable_sharepoint_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SharePoint provider is not enabled. Set ENABLE_SHAREPOINT_PROVIDER=true",
        )


# ============================================================================
# OAuth Flow Endpoints
# ============================================================================

@router.post("/auth/start", response_model=SharePointAuthStartResponse)
async def start_oauth_flow(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    Start OAuth flow for SharePoint/OneDrive access.

    Generates authorization URL and secure state token. Frontend should
    redirect user to the returned auth_url.

    **Security**: State token is stored server-side for CSRF protection.
    """
    graph_service = MicrosoftGraphService(db)

    # Generate secure state token
    state = generate_state_token()

    # Store state with user ID for validation in callback
    _oauth_states[state] = current_user.id

    # Generate Microsoft authorization URL
    auth_url = graph_service.generate_auth_url(state)

    return SharePointAuthStartResponse(auth_url=auth_url, state=state)


@router.post("/auth/callback", response_model=SharePointAuthCallbackResponse)
async def oauth_callback(
    callback_data: SharePointAuthCallbackRequest,
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    Handle OAuth callback from Microsoft.

    Exchanges authorization code for tokens, encrypts them, and stores
    in database. Returns connection_id for subsequent API calls.

    **Security**:
    - Validates state parameter against stored value
    - Tokens are encrypted before database storage
    - Returns only connection_id, never tokens
    """
    # Validate state parameter
    user_id = _oauth_states.pop(callback_data.state, None)
    if not user_id:
        raise BadRequestException("Invalid or expired state parameter")

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User not found")

    graph_service = MicrosoftGraphService(db)

    # Exchange code for tokens
    token_data, tenant_id = await graph_service.exchange_code_for_tokens(callback_data.code)

    # Encrypt tokens
    encryption_service = get_token_encryption_service()
    encrypted_tokens = encryption_service.encrypt_tokens(token_data)

    # Check if connection already exists for this user+tenant
    existing_connection = (
        db.query(ProviderConnection)
        .filter(
            ProviderConnection.provider == ProviderType.sharepoint,
            ProviderConnection.user_id == user_id,
            ProviderConnection.tenant_id == tenant_id,
        )
        .first()
    )

    if existing_connection:
        # Update existing connection with new tokens
        existing_connection.encrypted_tokens = encrypted_tokens
        db.commit()
        db.refresh(existing_connection)
        connection = existing_connection
    else:
        # Create new connection
        connection = ProviderConnection(
            provider=ProviderType.sharepoint,
            user_id=user_id,
            tenant_id=tenant_id,
            encrypted_tokens=encrypted_tokens,
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)

    return SharePointAuthCallbackResponse(
        connection_id=connection.id,
        tenant_id=connection.tenant_id,
        created_at=connection.created_at,
    )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    connection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    Disconnect and delete a SharePoint provider connection.

    Removes encrypted tokens from database. User will need to re-authorize
    to access SharePoint files again.

    **Security**: Users can only delete their own connections.
    """
    connection = (
        db.query(ProviderConnection)
        .filter(
            ProviderConnection.id == connection_id,
            ProviderConnection.user_id == current_user.id,
        )
        .first()
    )

    if not connection:
        raise NotFoundException("Connection not found")

    db.delete(connection)
    db.commit()


@router.get("/connections", response_model=ProviderConnectionsResponse)
async def list_connections(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    List user's SharePoint provider connections.

    Returns:
        List of connections (without tokens)
    """
    connections = (
        db.query(ProviderConnection)
        .filter(
            ProviderConnection.provider == ProviderType.sharepoint,
            ProviderConnection.user_id == current_user.id,
        )
        .all()
    )

    return ProviderConnectionsResponse(
        connections=[
            ProviderConnectionInfo(
                id=conn.id,
                provider=conn.provider.value,
                tenant_id=conn.tenant_id,
                created_at=conn.created_at,
                updated_at=conn.updated_at,
            )
            for conn in connections
        ]
    )


# ============================================================================
# OneDrive Browsing Endpoints
# ============================================================================

@router.get("/{connection_id}/onedrive/root", response_model=DriveInfo)
async def get_onedrive_root(
    connection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    Get user's OneDrive root drive information.

    Returns drive metadata including ID and name.
    """
    connection = _get_user_connection(db, connection_id, current_user.id)
    graph_service = MicrosoftGraphService(db)

    drive_data = await graph_service.get_onedrive_root(connection)

    return DriveInfo(
        id=drive_data["id"],
        name=drive_data.get("name", "My OneDrive"),
        description=drive_data.get("description"),
        drive_type=drive_data.get("driveType", "personal"),
        web_url=drive_data.get("webUrl"),
        owner=drive_data.get("owner"),
    )


@router.get("/{connection_id}/drives/{drive_id}/children", response_model=DriveItemsResponse)
async def get_drive_children(
    connection_id: UUID,
    drive_id: str,
    item_id: str = Query("root", description="Parent item ID"),
    page_token: Optional[str] = Query(None, description="Pagination token"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    List files and folders in a OneDrive/SharePoint location.

    Args:
        connection_id: Provider connection ID
        drive_id: Drive ID
        item_id: Parent folder ID (default: "root")
        page_token: Optional pagination token from previous response

    Returns:
        List of files and folders with sync status
    """
    connection = _get_user_connection(db, connection_id, current_user.id)
    graph_service = MicrosoftGraphService(db)

    response_data = await graph_service.get_drive_children(
        connection, drive_id, item_id, page_token
    )

    # Get list of already synced items for this drive
    synced_item_ids = set(
        db.query(ProviderItemRef.item_id)
        .filter(
            ProviderItemRef.connection_id == connection_id,
            ProviderItemRef.drive_id == drive_id,
        )
        .all()
    )
    synced_item_ids = {item_id[0] for item_id in synced_item_ids}

    items = []
    for item_data in response_data.get("value", []):
        # Determine item type
        item_type = DriveItemType.FOLDER if "folder" in item_data else DriveItemType.FILE

        # Parse timestamps
        last_modified = None
        if item_data.get("lastModifiedDateTime"):
            try:
                from dateutil import parser
                last_modified = parser.isoparse(item_data["lastModifiedDateTime"])
            except:
                pass

        items.append(
            DriveItem(
                id=item_data["id"],
                name=item_data["name"],
                type=item_type,
                size=item_data.get("size"),
                web_url=item_data.get("webUrl"),
                last_modified=last_modified,
                e_tag=item_data.get("eTag"),
                mime_type=item_data.get("file", {}).get("mimeType"),
                drive_id=drive_id,
                parent_reference=item_data.get("parentReference"),
                is_synced=item_data["id"] in synced_item_ids,
            )
        )

    # Extract next page link if present
    next_link = response_data.get("@odata.nextLink")

    return DriveItemsResponse(items=items, next_link=next_link)


# ============================================================================
# SharePoint Sites Browsing Endpoints
# ============================================================================

@router.get("/{connection_id}/sites/search", response_model=SitesResponse)
async def search_sites(
    connection_id: UUID,
    query: str = Query(..., min_length=1, max_length=255),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    Search for SharePoint sites by name.

    Args:
        connection_id: Provider connection ID
        query: Search query string

    Returns:
        List of matching SharePoint sites
    """
    connection = _get_user_connection(db, connection_id, current_user.id)
    graph_service = MicrosoftGraphService(db)

    response_data = await graph_service.search_sites(connection, query)

    sites = []
    for site_data in response_data.get("value", []):
        sites.append(
            SiteInfo(
                id=site_data["id"],
                name=site_data.get("name", ""),
                display_name=site_data.get("displayName", site_data.get("name", "")),
                web_url=site_data.get("webUrl", ""),
                description=site_data.get("description"),
            )
        )

    return SitesResponse(sites=sites)


@router.get("/{connection_id}/sites/{site_id}/drives", response_model=DrivesResponse)
async def get_site_drives(
    connection_id: UUID,
    site_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    Get document libraries (drives) for a SharePoint site.

    Args:
        connection_id: Provider connection ID
        site_id: SharePoint site ID

    Returns:
        List of drives (document libraries) in the site
    """
    connection = _get_user_connection(db, connection_id, current_user.id)
    graph_service = MicrosoftGraphService(db)

    response_data = await graph_service.get_site_drives(connection, site_id)

    drives = []
    for drive_data in response_data.get("value", []):
        drives.append(
            DriveInfo(
                id=drive_data["id"],
                name=drive_data.get("name", ""),
                description=drive_data.get("description"),
                drive_type=drive_data.get("driveType", "documentLibrary"),
                web_url=drive_data.get("webUrl"),
                owner=drive_data.get("owner"),
            )
        )

    return DrivesResponse(drives=drives)


@router.get("/{connection_id}/items/{drive_id}/{item_id}", response_model=DriveItem)
async def get_item_metadata(
    connection_id: UUID,
    drive_id: str,
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _enabled: None = Depends(check_sharepoint_enabled),
):
    """
    Get metadata for a specific file or folder.

    Args:
        connection_id: Provider connection ID
        drive_id: Drive ID
        item_id: Item ID

    Returns:
        Item metadata including size, timestamps, etc.
    """
    connection = _get_user_connection(db, connection_id, current_user.id)
    graph_service = MicrosoftGraphService(db)

    item_data = await graph_service.get_item_metadata(connection, drive_id, item_id)

    # Determine item type
    item_type = DriveItemType.FOLDER if "folder" in item_data else DriveItemType.FILE

    # Check if synced
    is_synced = (
        db.query(ProviderItemRef)
        .filter(
            ProviderItemRef.connection_id == connection_id,
            ProviderItemRef.drive_id == drive_id,
            ProviderItemRef.item_id == item_id,
        )
        .first()
    ) is not None

    # Parse timestamp
    last_modified = None
    if item_data.get("lastModifiedDateTime"):
        try:
            from dateutil import parser
            last_modified = parser.isoparse(item_data["lastModifiedDateTime"])
        except:
            pass

    return DriveItem(
        id=item_data["id"],
        name=item_data["name"],
        type=item_type,
        size=item_data.get("size"),
        web_url=item_data.get("webUrl"),
        last_modified=last_modified,
        e_tag=item_data.get("eTag"),
        mime_type=item_data.get("file", {}).get("mimeType"),
        drive_id=drive_id,
        parent_reference=item_data.get("parentReference"),
        is_synced=is_synced,
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _get_user_connection(
    db: Session, connection_id: UUID, user_id: UUID
) -> ProviderConnection:
    """
    Get and validate provider connection for the current user.

    Args:
        db: Database session
        connection_id: Connection ID
        user_id: Current user ID

    Returns:
        ProviderConnection

    Raises:
        NotFoundException: If connection not found or doesn't belong to user
    """
    connection = (
        db.query(ProviderConnection)
        .filter(
            ProviderConnection.id == connection_id,
            ProviderConnection.user_id == user_id,
        )
        .first()
    )

    if not connection:
        raise NotFoundException("Connection not found or access denied")

    return connection
