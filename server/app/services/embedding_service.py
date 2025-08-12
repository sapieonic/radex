import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID
import openai
from sqlalchemy.orm import Session
from app.models import Document, Embedding
from app.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.utils import chunk_text_with_metadata
from app.services.document_service import DocumentService

class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.document_service = DocumentService(db)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise BadRequestException(f"Failed to generate embeddings: {str(e)}")
    
    async def process_document_embeddings(
        self,
        document_id: UUID,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Embedding]:
        """Process a document and generate embeddings for all chunks"""
        # Get document
        document = self.document_service.get_document(document_id)
        if not document:
            raise NotFoundException("Document not found")
        
        # Check if embeddings already exist
        existing_embeddings = self.db.query(Embedding).filter(
            Embedding.document_id == document_id
        ).first()
        
        if existing_embeddings:
            # Delete existing embeddings to regenerate
            self.db.query(Embedding).filter(
                Embedding.document_id == document_id
            ).delete()
            self.db.commit()
        
        try:
            # Extract text from document
            text = self.document_service.extract_document_text(document_id)
            
            if not text.strip():
                raise BadRequestException("Document contains no extractable text")
            
            # Chunk the text
            chunks_with_metadata = chunk_text_with_metadata(
                text=text,
                chunk_size=chunk_size,
                overlap=overlap,
                document_id=str(document_id),
                document_title=document.filename
            )
            
            if not chunks_with_metadata:
                raise BadRequestException("No chunks generated from document text")
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk["text"] for chunk in chunks_with_metadata]
            embeddings = self.generate_embeddings(chunk_texts)
            
            # Save embeddings to database
            embedding_records = []
            for i, (chunk_data, embedding) in enumerate(zip(chunks_with_metadata, embeddings)):
                embedding_record = Embedding(
                    document_id=document_id,
                    chunk_index=i,
                    chunk_text=chunk_data["text"],
                    embedding=embedding,
                    embed_metadata=chunk_data["metadata"]
                )
                embedding_records.append(embedding_record)
                self.db.add(embedding_record)
            
            self.db.commit()
            
            # Refresh all records
            for record in embedding_records:
                self.db.refresh(record)
            
            return embedding_records
            
        except Exception as e:
            self.db.rollback()
            raise BadRequestException(f"Failed to process document embeddings: {str(e)}")
    
    def get_document_embeddings(self, document_id: UUID) -> List[Embedding]:
        """Get all embeddings for a document"""
        return self.db.query(Embedding).filter(
            Embedding.document_id == document_id
        ).order_by(Embedding.chunk_index).all()
    
    def delete_document_embeddings(self, document_id: UUID) -> bool:
        """Delete all embeddings for a document"""
        deleted_count = self.db.query(Embedding).filter(
            Embedding.document_id == document_id
        ).delete()
        
        self.db.commit()
        return deleted_count > 0
    
    def search_similar_chunks(
        self,
        query_embedding: List[float],
        folder_ids: List[UUID],
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity"""
        try:
            # Convert similarity threshold to distance threshold
            # cosine distance = 1 - cosine similarity
            max_distance = 1 - min_similarity
            
            # Build SQL query for vector similarity search
            folder_ids_str = ",".join([f"'{folder_id}'" for folder_id in folder_ids])
            
            query = f"""
                SELECT 
                    e.id,
                    e.document_id,
                    e.chunk_index,
                    e.chunk_text,
                    e.embed_metadata,
                    d.filename,
                    d.folder_id,
                    f.name as folder_name,
                    (1 - (e.embedding <=> %s::vector)) as similarity_score
                FROM embeddings e
                JOIN documents d ON e.document_id = d.id
                JOIN folders f ON d.folder_id = f.id
                WHERE d.folder_id IN ({folder_ids_str})
                AND (1 - (e.embedding <=> %s::vector)) >= %s
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
            """
            
            result = self.db.execute(
                query,
                (query_embedding, query_embedding, min_similarity, query_embedding, limit)
            )
            
            results = []
            for row in result:
                results.append({
                    "id": row.id,
                    "document_id": row.document_id,
                    "document_name": row.filename,
                    "folder_id": row.folder_id,
                    "folder_name": row.folder_name,
                    "chunk_index": row.chunk_index,
                    "chunk_text": row.chunk_text,
                    "similarity_score": float(row.similarity_score),
                    "metadata": row.embed_metadata
                })
            
            return results
            
        except Exception as e:
            raise BadRequestException(f"Failed to search similar chunks: {str(e)}")
    
    def get_embedding_stats(self, document_id: UUID) -> Dict[str, Any]:
        """Get statistics about embeddings for a document"""
        embeddings = self.get_document_embeddings(document_id)
        
        if not embeddings:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "average_chunk_size": 0
            }
        
        total_characters = sum(len(emb.chunk_text) for emb in embeddings)
        
        return {
            "total_chunks": len(embeddings),
            "total_characters": total_characters,
            "average_chunk_size": total_characters // len(embeddings) if embeddings else 0
        }
    
    async def reprocess_document_embeddings(
        self,
        document_id: UUID,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Embedding]:
        """Reprocess embeddings for a document with new parameters"""
        return await self.process_document_embeddings(document_id, chunk_size, overlap)