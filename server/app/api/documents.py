from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import Document, DocumentUploadResponse
from app.models import User as UserModel
from app.core.dependencies import get_current_active_user
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException
from app.services.permission_service import PermissionService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
import io

router = APIRouter()

@router.post("/folders/{folder_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    folder_id: UUID,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a document to a folder"""
    permission_service = PermissionService(db)
    document_service = DocumentService(db)
    embedding_service = EmbeddingService(db)
    
    # Check write permission for folder
    permission_service.check_folder_access(current_user.id, folder_id, "write")
    
    # Upload document
    document = await document_service.upload_document(
        file=file,
        folder_id=folder_id,
        uploaded_by=current_user.id
    )
    
    # Start background task to process embeddings
    try:
        await embedding_service.process_document_embeddings(document.id)
    except Exception as e:
        # Log the error but don't fail the upload
        print(f"Failed to process embeddings for document {document.id}: {e}")
    
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        file_size=document.file_size,
        file_type=document.file_type,
        folder_id=document.folder_id,
        message="Document uploaded successfully"
    )

@router.get("/documents/{document_id}", response_model=Document)
def get_document_metadata(
    document_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document metadata"""
    permission_service = PermissionService(db)
    document_service = DocumentService(db)
    
    document = document_service.get_document(document_id)
    if not document:
        raise NotFoundException("Document not found")
    
    # Check read permission for folder
    permission_service.check_folder_access(current_user.id, document.folder_id, "read")
    
    return document

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download a document"""
    permission_service = PermissionService(db)
    document_service = DocumentService(db)
    
    document = document_service.get_document(document_id)
    if not document:
        raise NotFoundException("Document not found")
    
    # Check read permission for folder
    permission_service.check_folder_access(current_user.id, document.folder_id, "read")
    
    # Download from MinIO
    file_response, filename, file_type = document_service.download_document(document_id)
    
    # Create streaming response
    def iterfile():
        for chunk in file_response.stream(32*1024):
            yield chunk
    
    # Determine media type
    media_type = "application/octet-stream"
    if file_type:
        type_mapping = {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "html": "text/html",
            "md": "text/markdown"
        }
        media_type = type_mapping.get(file_type.lower(), "application/octet-stream")
    
    return StreamingResponse(
        iterfile(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    permission_service = PermissionService(db)
    document_service = DocumentService(db)
    
    document = document_service.get_document(document_id)
    if not document:
        raise NotFoundException("Document not found")
    
    # Check delete permission for folder
    permission_service.check_folder_access(current_user.id, document.folder_id, "delete")
    
    # Delete document
    document_service.delete_document(document_id)

@router.get("/folders/{folder_id}/documents", response_model=List[Document])
def list_folder_documents(
    folder_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all documents in a folder"""
    permission_service = PermissionService(db)
    document_service = DocumentService(db)
    
    # Check read permission for folder
    permission_service.check_folder_access(current_user.id, folder_id, "read")
    
    documents = document_service.get_documents_in_folder(folder_id)
    return documents

@router.post("/documents/{document_id}/reprocess-embeddings", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_document_embeddings(
    document_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Reprocess embeddings for a document"""
    permission_service = PermissionService(db)
    document_service = DocumentService(db)
    embedding_service = EmbeddingService(db)
    
    document = document_service.get_document(document_id)
    if not document:
        raise NotFoundException("Document not found")
    
    # Check write permission for folder (needed to reprocess)
    permission_service.check_folder_access(current_user.id, document.folder_id, "write")
    
    # Reprocess embeddings
    try:
        await embedding_service.reprocess_document_embeddings(document_id)
        return {"message": "Embeddings reprocessed successfully"}
    except Exception as e:
        raise BadRequestException(f"Failed to reprocess embeddings: {str(e)}")

@router.get("/documents/{document_id}/embeddings/stats")
def get_document_embedding_stats(
    document_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get embedding statistics for a document"""
    permission_service = PermissionService(db)
    document_service = DocumentService(db)
    embedding_service = EmbeddingService(db)
    
    document = document_service.get_document(document_id)
    if not document:
        raise NotFoundException("Document not found")
    
    # Check read permission for folder
    permission_service.check_folder_access(current_user.id, document.folder_id, "read")
    
    stats = embedding_service.get_embedding_stats(document_id)
    return stats