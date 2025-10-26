from sqlalchemy import Column, String, Boolean, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum

class AuthProvider(str, enum.Enum):
    """Authentication provider types"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    PASSWORD = "password"  # Legacy support

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)  # Now nullable for Firebase users

    # Firebase authentication fields
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)  # Firebase UID as primary identifier
    auth_provider = Column(Enum(AuthProvider, values_callable=lambda x: [e.value for e in x]), nullable=True, default=AuthProvider.PASSWORD)

    # Legacy password field - now nullable
    hashed_password = Column(String(255), nullable=True)

    # User profile fields from Firebase
    display_name = Column(String(255), nullable=True)
    photo_url = Column(String(512), nullable=True)

    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Email verification status
    email_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    provider_connections = relationship("ProviderConnection", back_populates="user", cascade="all, delete-orphan")