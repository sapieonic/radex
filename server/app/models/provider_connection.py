"""
Provider Connection Model

Stores encrypted OAuth tokens and connection metadata for external file providers
like Microsoft SharePoint/OneDrive. Tokens are encrypted using Fernet before storage.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class ProviderType(str, enum.Enum):
    """Supported file provider types."""
    sharepoint = "sharepoint"


class ProviderConnection(Base):
    """
    Stores user connections to external file providers.

    Each connection represents a user's authorization to access files from
    an external provider (e.g., Microsoft 365 tenant). Tokens are encrypted
    before storage and never exposed to the frontend.
    """
    __tablename__ = "provider_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(SQLEnum(ProviderType), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(255), nullable=False, comment="Microsoft 365 tenant ID")

    # Encrypted token storage - contains Fernet-encrypted JSON with access_token, refresh_token, expires_at
    encrypted_tokens = Column(Text, nullable=False, comment="Fernet-encrypted token data")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="provider_connections")
    synced_items = relationship("ProviderItemRef", back_populates="connection", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_provider_connections_user_id', 'user_id'),
        Index('ix_provider_connections_provider_user', 'provider', 'user_id'),
        # Ensure one connection per user per provider per tenant
        Index('uix_provider_user_tenant', 'provider', 'user_id', 'tenant_id', unique=True),
    )
