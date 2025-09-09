from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID

from app.models import ConfluenceType, ImportType, SyncStatus


# Authentication Schemas
class ConfluenceAuthRequest(BaseModel):
    confluence_type: ConfluenceType
    base_url: str
    email: Optional[str] = None
    api_token: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

class ConfluenceAuthResponse(BaseModel):
    id: UUID
    confluence_type: ConfluenceType
    base_url: str
    email: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_valid: bool

class ConfluenceCredentialList(BaseModel):
    credentials: List[ConfluenceAuthResponse]


# Space and Page Schemas
class ConfluenceSpace(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    homepage_id: Optional[str] = None

class ConfluencePage(BaseModel):
    id: str
    title: str
    space_key: str
    parent_id: Optional[str] = None
    version: int
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    has_children: bool = False
    has_attachments: bool = False


# Import Schemas
class ConfluenceImportRequest(BaseModel):
    credential_id: UUID
    folder_id: UUID
    import_type: ImportType
    space_key: Optional[str] = None
    page_id: Optional[str] = None
    include_attachments: bool = True
    include_comments: bool = False
    recursive: bool = True

class ConfluenceImportResponse(BaseModel):
    id: UUID
    import_type: ImportType
    sync_status: SyncStatus
    total_pages: int = 0
    processed_pages: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    last_sync_at: Optional[datetime] = None

class ConfluenceImportStatus(BaseModel):
    id: UUID
    status: SyncStatus
    total_pages: int
    processed_pages: int
    error_message: Optional[str] = None
    created_at: datetime
    last_sync_at: Optional[datetime] = None
    progress_percentage: float = Field(default=0.0)
    
    @property
    def progress_percentage(self) -> float:
        if self.total_pages == 0:
            return 0.0
        return (self.processed_pages / self.total_pages) * 100


# Search and Discovery Schemas
class ConfluenceSearchRequest(BaseModel):
    credential_id: UUID
    query: str
    search_type: Literal["cql", "text"] = "text"
    limit: int = Field(default=50, ge=1, le=100)

class ConfluenceSearchResult(BaseModel):
    id: str
    title: str
    space_key: str
    space_name: str
    excerpt: Optional[str] = None
    url: Optional[str] = None
    last_modified: Optional[datetime] = None


# Sync Schemas
class ConfluenceSyncRequest(BaseModel):
    import_id: UUID
    force_full_sync: bool = False

class ConfluenceSyncResponse(BaseModel):
    import_id: UUID
    status: str
    pages_updated: int
    pages_added: int
    pages_deleted: int
    sync_started_at: datetime
    sync_completed_at: Optional[datetime] = None


# Batch Import Schema
class ConfluenceBatchImportRequest(BaseModel):
    credential_id: UUID
    folder_id: UUID
    imports: List[Dict[str, Any]]
    
class ConfluenceBatchImportItem(BaseModel):
    import_type: ImportType
    space_key: Optional[str] = None
    page_id: Optional[str] = None

class ConfluenceBatchImportResponse(BaseModel):
    job_ids: List[UUID]
    total_jobs: int
    status: str