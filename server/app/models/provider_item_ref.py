"""
Provider Item Reference Model

Tracks files synced from external providers to maintain idempotency
and enable change detection for future sync operations.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base
from app.models.provider_connection import ProviderType


class ProviderItemRef(Base):
    """
    Reference to files synced from external providers.

    Used for idempotency checking - prevents duplicate imports of the same file.
    Stores provider-specific identifiers and metadata for change detection.
    """
    __tablename__ = "provider_item_refs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Provider identification
    provider = Column(SQLEnum(ProviderType), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("provider_connections.id", ondelete="CASCADE"), nullable=False)

    # Link to imported document
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    # Microsoft Graph identifiers
    drive_id = Column(String(255), nullable=False, comment="SharePoint/OneDrive drive ID")
    item_id = Column(String(255), nullable=False, comment="SharePoint/OneDrive item ID")
    etag = Column(String(255), nullable=True, comment="Entity tag for change detection")

    # File metadata (cached for display)
    name = Column(String(500), nullable=True)
    size = Column(BigInteger, nullable=True)
    last_modified = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String(255), nullable=True, comment="QuickXorHash for content verification")

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    connection = relationship("ProviderConnection", back_populates="synced_items")
    document = relationship("Document")

    # Indexes
    __table_args__ = (
        # Unique constraint: prevent duplicate imports
        Index('uix_provider_drive_item', 'provider', 'drive_id', 'item_id', unique=True),
        Index('ix_provider_item_refs_connection_id', 'connection_id'),
        Index('ix_provider_item_refs_document_id', 'document_id'),
    )
