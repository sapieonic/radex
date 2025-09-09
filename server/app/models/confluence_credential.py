from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid

from app.database import Base


class ConfluenceType(str, enum.Enum):
    CLOUD = "cloud"
    SERVER = "server"
    DATA_CENTER = "data_center"


class ConfluenceCredential(Base):
    __tablename__ = "confluence_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    confluence_type = Column(SQLEnum(ConfluenceType), nullable=False)
    base_url = Column(String(255), nullable=False)
    email = Column(String(255))
    api_token_encrypted = Column(Text)
    oauth_token_encrypted = Column(Text)
    oauth_refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="confluence_credentials")
    imports = relationship("ConfluenceImport", back_populates="credential", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ConfluenceCredential(id={self.id}, user_id={self.user_id}, base_url={self.base_url})>"