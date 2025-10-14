from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID

class RAGQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    folder_ids: Optional[List[UUID]] = None
    limit: int = Field(default=10, ge=1, le=50)
    min_relevance_score: float = Field(default=0.7, ge=0.0, le=1.0)

class RAGChunk(BaseModel):
    document_id: UUID
    document_name: str
    folder_id: UUID
    folder_name: str
    chunk_text: str
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: List[RAGChunk]
    total_chunks: int
    processing_time: float

class EmbeddingStatus(BaseModel):
    document_id: UUID
    status: str  # "pending", "processing", "completed", "failed"
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None
    error_message: Optional[str] = None

# Chat-specific schemas
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=10000)

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_items=1, max_items=100)
    folder_ids: List[UUID] = Field(..., min_items=1)
    limit: int = Field(default=10, ge=1, le=50)
    min_relevance_score: float = Field(default=0.7, ge=0.0, le=1.0)

class ChatResponse(BaseModel):
    role: Literal["assistant"]
    content: str
    sources: List[RAGChunk]
    total_chunks: int
    processing_time: float
    reformulated_query: Optional[str] = None  # The query used for vector search