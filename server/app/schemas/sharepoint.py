"""
Pydantic schemas for SharePoint/OneDrive provider endpoints.

Defines request/response models for OAuth flow, file browsing, and sync operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# Provider Configuration
# ============================================================================

class ProviderInfo(BaseModel):
    """Information about an available file provider."""
    provider: str = Field(..., description="Provider identifier (e.g., 'sharepoint')")
    display_name: str = Field(..., description="Human-readable provider name")
    is_enabled: bool = Field(..., description="Whether provider is available for use")
    is_configured: bool = Field(..., description="Whether required credentials are configured")

    class Config:
        from_attributes = True


class ProvidersConfigResponse(BaseModel):
    """Response containing all available providers."""
    providers: List[ProviderInfo] = Field(..., description="List of available file providers")


# ============================================================================
# OAuth Flow
# ============================================================================

class SharePointAuthStartResponse(BaseModel):
    """Response from OAuth start endpoint."""
    auth_url: str = Field(..., description="Microsoft OAuth authorization URL to redirect user to")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")


class SharePointAuthCallbackRequest(BaseModel):
    """Request body for OAuth callback endpoint."""
    code: str = Field(..., description="Authorization code from Microsoft OAuth")
    state: str = Field(..., description="State parameter to validate against CSRF")


class SharePointAuthCallbackResponse(BaseModel):
    """Response from OAuth callback endpoint."""
    connection_id: UUID = Field(..., description="Unique connection identifier for subsequent API calls")
    tenant_id: str = Field(..., description="Microsoft 365 tenant ID")
    created_at: datetime = Field(..., description="Connection creation timestamp")


class ProviderConnectionInfo(BaseModel):
    """Information about a provider connection."""
    id: UUID
    provider: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProviderConnectionsResponse(BaseModel):
    """Response containing user's provider connections."""
    connections: List[ProviderConnectionInfo]


# ============================================================================
# File/Folder Items
# ============================================================================

class DriveItemType(str, Enum):
    """Type of SharePoint/OneDrive item."""
    FILE = "file"
    FOLDER = "folder"


class DriveItem(BaseModel):
    """Represents a file or folder in SharePoint/OneDrive."""
    id: str = Field(..., description="Microsoft Graph item ID")
    name: str = Field(..., description="Item name")
    type: DriveItemType = Field(..., description="Item type (file or folder)")
    size: Optional[int] = Field(None, description="File size in bytes (null for folders)")
    web_url: Optional[str] = Field(None, description="Web URL to view item")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    e_tag: Optional[str] = Field(None, description="Entity tag for change detection")
    mime_type: Optional[str] = Field(None, description="MIME type for files")

    # SharePoint-specific metadata
    drive_id: str = Field(..., description="Parent drive ID")
    parent_reference: Optional[dict] = Field(None, description="Parent folder reference")

    # Sync status
    is_synced: bool = Field(False, description="Whether this item is already synced")

    class Config:
        from_attributes = True


class DriveItemsResponse(BaseModel):
    """Response containing list of drive items."""
    items: List[DriveItem] = Field(..., description="List of files and folders")
    next_link: Optional[str] = Field(None, description="URL for next page (pagination)")


# ============================================================================
# Drives & Sites
# ============================================================================

class DriveInfo(BaseModel):
    """Represents a SharePoint document library or OneDrive."""
    id: str = Field(..., description="Drive ID")
    name: str = Field(..., description="Drive name (e.g., 'Documents', 'My OneDrive')")
    description: Optional[str] = Field(None, description="Drive description")
    drive_type: str = Field(..., description="Type: 'personal' (OneDrive) or 'documentLibrary' (SharePoint)")
    web_url: Optional[str] = Field(None, description="Web URL to view drive")
    owner: Optional[dict] = Field(None, description="Drive owner information")

    class Config:
        from_attributes = True


class DrivesResponse(BaseModel):
    """Response containing list of drives."""
    drives: List[DriveInfo] = Field(..., description="List of accessible drives")


class SiteInfo(BaseModel):
    """Represents a SharePoint site."""
    id: str = Field(..., description="Site ID")
    name: str = Field(..., description="Site name")
    display_name: str = Field(..., description="Site display name")
    web_url: str = Field(..., description="SharePoint site URL")
    description: Optional[str] = Field(None, description="Site description")

    class Config:
        from_attributes = True


class SitesResponse(BaseModel):
    """Response containing list of SharePoint sites."""
    sites: List[SiteInfo] = Field(..., description="List of accessible SharePoint sites")


# ============================================================================
# Sync/Import
# ============================================================================

class SharePointItemToSync(BaseModel):
    """Represents a single SharePoint item to sync."""
    drive_id: str = Field(..., description="Microsoft Graph drive ID")
    item_id: str = Field(..., description="Microsoft Graph item ID")
    e_tag: Optional[str] = Field(None, description="Entity tag for change detection")

    @validator('drive_id', 'item_id')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class SyncImportRequest(BaseModel):
    """Request to import files from SharePoint/OneDrive."""
    connection_id: UUID = Field(..., description="Provider connection ID")
    folder_id: UUID = Field(..., description="Target RADEX folder ID for imported files")
    items: List[SharePointItemToSync] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of items to sync (max 100 per request)"
    )

    @validator('items')
    def validate_items_not_empty(cls, v):
        if not v:
            raise ValueError('At least one item must be provided')
        return v


class SyncedItemInfo(BaseModel):
    """Information about a synced item."""
    sharepoint_item_id: str = Field(..., description="SharePoint item ID")
    document_id: UUID = Field(..., description="RADEX document ID")
    filename: str = Field(..., description="File name")
    status: str = Field(..., description="Sync status: 'success', 'skipped', or 'failed'")
    message: Optional[str] = Field(None, description="Status message or error description")


class SyncImportResponse(BaseModel):
    """Response from sync/import operation."""
    total: int = Field(..., description="Total items requested")
    succeeded: int = Field(..., description="Successfully synced items")
    skipped: int = Field(..., description="Skipped items (already synced)")
    failed: int = Field(..., description="Failed items")
    results: List[SyncedItemInfo] = Field(..., description="Detailed results for each item")


# ============================================================================
# Browsing Requests
# ============================================================================

class GetOneDriveRootRequest(BaseModel):
    """Request for OneDrive root folder contents."""
    connection_id: UUID = Field(..., description="Provider connection ID")


class GetDriveChildrenRequest(BaseModel):
    """Request for children of a drive item."""
    connection_id: UUID = Field(..., description="Provider connection ID")
    drive_id: str = Field(..., description="Drive ID")
    item_id: Optional[str] = Field("root", description="Item ID (default: 'root')")
    page_token: Optional[str] = Field(None, description="Pagination token for next page")


class SearchSitesRequest(BaseModel):
    """Request to search SharePoint sites."""
    connection_id: UUID = Field(..., description="Provider connection ID")
    query: str = Field(..., min_length=1, max_length=255, description="Search query")


class GetSiteDrivesRequest(BaseModel):
    """Request for drives in a SharePoint site."""
    connection_id: UUID = Field(..., description="Provider connection ID")
    site_id: str = Field(..., description="SharePoint site ID")


class GetItemMetadataRequest(BaseModel):
    """Request for item metadata."""
    connection_id: UUID = Field(..., description="Provider connection ID")
    drive_id: str = Field(..., description="Drive ID")
    item_id: str = Field(..., description="Item ID")
