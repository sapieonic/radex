from sqlalchemy import Column, String, DateTime, func, ForeignKey, BigInteger, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(BigInteger)
    file_path = Column(String, nullable=False)
    doc_metadata = Column("metadata", JSON, default={})
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    folder = relationship("Folder", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")