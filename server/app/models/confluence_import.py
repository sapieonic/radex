from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid

from app.database import Base


class ImportType(str, enum.Enum):
    PAGE = "page"
    SPACE = "space"
    PAGE_TREE = "page_tree"


class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ConfluenceImport(Base):
    __tablename__ = "confluence_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credential_id = Column(UUID(as_uuid=True), ForeignKey("confluence_credentials.id", ondelete="CASCADE"))
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    space_key = Column(String(50))
    page_id = Column(String(50))
    import_type = Column(SQLEnum(ImportType), nullable=False)
    last_sync_at = Column(DateTime)
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING)
    total_pages = Column(Integer, default=0)
    processed_pages = Column(Integer, default=0)
    error_message = Column(Text)
    import_metadata = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    credential = relationship("ConfluenceCredential", back_populates="imports")
    folder = relationship("Folder", back_populates="confluence_imports")
    pages = relationship("ConfluencePage", back_populates="import_job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ConfluenceImport(id={self.id}, type={self.import_type}, status={self.sync_status})>"