from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class FolderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None

class FolderCreate(FolderBase):
    pass

class FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

class FolderInDB(FolderBase):
    id: UUID
    owner_id: UUID
    path: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Folder(FolderInDB):
    pass

class FolderWithPermissions(Folder):
    can_read: bool = False
    can_write: bool = False
    can_delete: bool = False
    is_admin: bool = False

class PermissionGrant(BaseModel):
    user_id: UUID
    can_read: bool = False
    can_write: bool = False
    can_delete: bool = False
    is_admin: bool = False

class PermissionInfo(BaseModel):
    id: UUID
    user_id: UUID
    folder_id: UUID
    can_read: bool
    can_write: bool
    can_delete: bool
    is_admin: bool
    granted_by: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True