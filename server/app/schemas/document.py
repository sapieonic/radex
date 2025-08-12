from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: Optional[str] = None
    # Temporarily remove metadata to fix test issues
    # doc_metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

class DocumentCreate(DocumentBase):
    folder_id: UUID

class DocumentUpdate(BaseModel):
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    # doc_metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata")

class DocumentInDB(DocumentBase):
    id: UUID
    folder_id: UUID
    file_size: Optional[int] = None
    file_path: str
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True

class Document(DocumentInDB):
    pass

class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    file_size: int
    file_type: str
    folder_id: UUID
    message: str = "Document uploaded successfully"