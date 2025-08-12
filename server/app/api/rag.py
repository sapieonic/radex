from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import RAGQuery, RAGResponse
from app.models import User as UserModel
from app.core.dependencies import get_current_active_user
from app.core.exceptions import BadRequestException, PermissionDeniedException
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/query", response_model=RAGResponse)
async def rag_query(
    rag_query: RAGQuery,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a RAG query and get an AI-generated response with sources"""
    rag_service = RAGService(db)
    
    try:
        response = await rag_service.query(
            user_id=current_user.id,
            rag_query=rag_query
        )
        return response
    except (BadRequestException, PermissionDeniedException) as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/folders")
def get_queryable_folders(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get list of folders that user can query"""
    rag_service = RAGService(db)
    
    folders = rag_service.get_queryable_folders(current_user.id)
    return folders

@router.post("/suggest-queries")
async def suggest_related_queries(
    original_query: str,
    folder_ids: List[str] = None,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, List[str]]:
    """Get suggested related queries based on available content"""
    rag_service = RAGService(db)
    
    # Convert string UUIDs to UUID objects if provided
    folder_uuid_list = None
    if folder_ids:
        try:
            from uuid import UUID
            folder_uuid_list = [UUID(folder_id) for folder_id in folder_ids]
        except ValueError:
            raise BadRequestException("Invalid folder ID format")
    
    suggestions = await rag_service.suggest_related_queries(
        user_id=current_user.id,
        original_query=original_query,
        folder_ids=folder_uuid_list
    )
    
    return {"suggestions": suggestions}

@router.get("/health")
def rag_health_check(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check RAG system health and user's access"""
    rag_service = RAGService(db)
    
    # Get basic stats about user's accessible content
    queryable_folders = rag_service.get_queryable_folders(current_user.id)
    
    total_folders = len(queryable_folders)
    queryable_folders_count = len([f for f in queryable_folders if f["can_query"]])
    total_documents = sum(f["document_count"] for f in queryable_folders)
    total_embeddings = sum(f["embedding_count"] for f in queryable_folders)
    
    return {
        "status": "healthy",
        "user_id": str(current_user.id),
        "accessible_folders": total_folders,
        "queryable_folders": queryable_folders_count,
        "total_documents": total_documents,
        "total_embeddings": total_embeddings,
        "can_query": queryable_folders_count > 0
    }