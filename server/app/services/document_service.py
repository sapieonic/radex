import os
import tempfile
from typing import List, Optional, BinaryIO
from uuid import UUID
import hashlib
from sqlalchemy.orm import Session
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from app.models import Document, Folder
from app.config import settings
from app.core.exceptions import NotFoundException, BadRequestException
from app.utils import (
    get_file_type,
    is_supported_file_type,
    extract_text_from_file,
    validate_file_size
)

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the MinIO bucket exists"""
        try:
            if not self.minio_client.bucket_exists(settings.minio_bucket):
                self.minio_client.make_bucket(settings.minio_bucket)
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def _generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _get_object_name(self, document_id: str, filename: str) -> str:
        """Generate object name for MinIO storage"""
        return f"documents/{document_id}/{filename}"
    
    async def upload_document(
        self,
        file: UploadFile,
        folder_id: UUID,
        uploaded_by: UUID
    ) -> Document:
        """Upload a document to MinIO and save metadata to database"""
        # Validate folder exists
        folder = self.db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise NotFoundException("Folder not found")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if not validate_file_size(file_size):
            raise BadRequestException("File size exceeds maximum limit (50MB)")
        
        # Get file type
        file_type = get_file_type(file.filename)
        if not file_type:
            raise BadRequestException("Could not determine file type")
        
        # Generate file hash for deduplication
        file_hash = self._generate_file_hash(file_content)
        
        # Check if file already exists in folder
        existing_doc = self.db.query(Document).filter(
            Document.folder_id == folder_id,
            Document.filename == file.filename
        ).first()
        
        if existing_doc:
            raise BadRequestException("File with this name already exists in the folder")
        
        # Create document record
        document = Document(
            folder_id=folder_id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            file_path="",  # Will be updated after MinIO upload
            doc_metadata={"file_hash": file_hash},
            uploaded_by=uploaded_by
        )
        
        self.db.add(document)
        self.db.flush()  # Get the document ID
        
        # Upload to MinIO
        object_name = self._get_object_name(str(document.id), file.filename)
        
        try:
            # Create a temporary file for upload
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(file_content)
                temp_file.seek(0)
                
                self.minio_client.fput_object(
                    settings.minio_bucket,
                    object_name,
                    temp_file.name,
                    content_type=file.content_type
                )
            
            # Update document with file path
            document.file_path = object_name
            self.db.commit()
            self.db.refresh(document)
            
            return document
            
        except S3Error as e:
            self.db.rollback()
            raise BadRequestException(f"Failed to upload file: {str(e)}")
    
    def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents_in_folder(self, folder_id: UUID) -> List[Document]:
        """Get all documents in a folder"""
        return self.db.query(Document).filter(Document.folder_id == folder_id).all()
    
    def download_document(self, document_id: UUID) -> tuple[BinaryIO, str, str]:
        """Download document from MinIO"""
        document = self.get_document(document_id)
        if not document:
            raise NotFoundException("Document not found")
        
        try:
            response = self.minio_client.get_object(
                settings.minio_bucket,
                document.file_path
            )
            return response, document.filename, document.file_type
            
        except S3Error as e:
            raise BadRequestException(f"Failed to download file: {str(e)}")
    
    def delete_document(self, document_id: UUID) -> bool:
        """Delete document from both database and MinIO"""
        document = self.get_document(document_id)
        if not document:
            raise NotFoundException("Document not found")
        
        try:
            # Delete from MinIO
            self.minio_client.remove_object(
                settings.minio_bucket,
                document.file_path
            )
            
            # Delete from database (this will cascade to embeddings)
            self.db.delete(document)
            self.db.commit()
            
            return True
            
        except S3Error as e:
            self.db.rollback()
            raise BadRequestException(f"Failed to delete file: {str(e)}")
    
    def extract_document_text(self, document_id: UUID) -> str:
        """Extract text content from document"""
        document = self.get_document(document_id)
        if not document:
            raise NotFoundException("Document not found")
        
        if not is_supported_file_type(document.file_type):
            raise BadRequestException(f"File type '{document.file_type}' is not supported for text extraction")
        
        try:
            # Download file to temporary location
            with tempfile.NamedTemporaryFile(suffix=f".{document.file_type}") as temp_file:
                response = self.minio_client.get_object(
                    settings.minio_bucket,
                    document.file_path
                )
                
                # Write content to temp file
                for chunk in response.stream(32*1024):
                    temp_file.write(chunk)
                temp_file.flush()
                
                # Extract text
                text = extract_text_from_file(temp_file.name, document.file_type)
                return text
                
        except S3Error as e:
            raise BadRequestException(f"Failed to download file for text extraction: {str(e)}")
        except Exception as e:
            raise BadRequestException(f"Failed to extract text: {str(e)}")
    
    def update_document_metadata(
        self,
        document_id: UUID,
        metadata: dict
    ) -> Document:
        """Update document metadata"""
        document = self.get_document(document_id)
        if not document:
            raise NotFoundException("Document not found")
        
        # Merge with existing metadata
        existing_metadata = document.doc_metadata or {}
        existing_metadata.update(metadata)
        document.doc_metadata = existing_metadata
        
        self.db.commit()
        self.db.refresh(document)
        
        return document