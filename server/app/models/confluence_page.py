from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class ConfluencePage(Base):
    __tablename__ = "confluence_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id = Column(UUID(as_uuid=True), ForeignKey("confluence_imports.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"))
    confluence_page_id = Column(String(50), nullable=False)
    confluence_space_key = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    parent_page_id = Column(String(50))
    version_number = Column(String(20))
    author_email = Column(String(255))
    created_date = Column(DateTime)
    modified_date = Column(DateTime)
    has_attachments = Column(Boolean, default=False)
    content_hash = Column(String(64))  # SHA256 hash for change detection
    page_metadata = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    import_job = relationship("ConfluenceImport", back_populates="pages")
    document = relationship("Document", backref="confluence_page", uselist=False)
    
    def __repr__(self):
        return f"<ConfluencePage(id={self.id}, page_id={self.confluence_page_id}, title={self.title})>"