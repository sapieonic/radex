"""
Provider Configuration Model

Stores non-secret configuration for external file providers.
Secrets (client IDs, secrets) remain in environment variables.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class ProviderConfig(Base):
    """
    Configuration for external file providers.

    Stores non-secret metadata like OAuth URLs, API endpoints, and default scopes.
    Client IDs and secrets are stored in environment variables, not the database.
    """
    __tablename__ = "provider_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Provider identification
    provider = Column(String(50), nullable=False, unique=True, comment="Provider type (e.g., 'sharepoint')")
    display_name = Column(String(255), nullable=False, comment="Human-readable name")

    # OAuth configuration (non-secret)
    auth_url = Column(String(500), nullable=False, comment="OAuth authorization endpoint")
    token_url = Column(String(500), nullable=False, comment="OAuth token endpoint")

    # API configuration
    graph_base_url = Column(String(500), nullable=False, comment="Microsoft Graph API base URL")
    default_scopes = Column(ARRAY(String), nullable=False, comment="Default OAuth scopes")

    # Feature flags
    is_enabled = Column(Boolean, default=False, nullable=False, comment="DB-level kill switch")

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
