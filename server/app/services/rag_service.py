import time
from typing import List, Dict, Any, Optional
from uuid import UUID
import openai
from sqlalchemy.orm import Session
from app.models import User
from app.config import settings
from app.core.exceptions import BadRequestException, PermissionDeniedException
from app.services.permission_service import PermissionService
from app.services.embedding_service import EmbeddingService
from app.schemas import RAGQuery, RAGResponse, RAGChunk

class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.permission_service = PermissionService(db)
        self.embedding_service = EmbeddingService(db)
    
    async def query(
        self,
        user_id: UUID,
        rag_query: RAGQuery
    ) -> RAGResponse:
        """Process a RAG query and return response with sources"""
        start_time = time.time()
        
        try:
            # Get accessible folders for the user
            accessible_folders = self._get_accessible_folders(user_id, rag_query.folder_ids)
            
            if not accessible_folders:
                raise PermissionDeniedException("No accessible folders found for query")
            
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embeddings([rag_query.query])[0]
            
            # Search for similar chunks
            similar_chunks = self.embedding_service.search_similar_chunks(
                query_embedding=query_embedding,
                folder_ids=accessible_folders,
                limit=rag_query.limit,
                min_similarity=rag_query.min_relevance_score
            )
            
            if not similar_chunks:
                return RAGResponse(
                    query=rag_query.query,
                    answer="No relevant documents found for your query.",
                    sources=[],
                    total_chunks=0,
                    processing_time=time.time() - start_time
                )
            
            # Generate answer using OpenAI
            answer = await self._generate_answer(rag_query.query, similar_chunks)
            
            # Format sources
            sources = []
            for chunk in similar_chunks:
                source = RAGChunk(
                    document_id=chunk["document_id"],
                    document_name=chunk["document_name"],
                    folder_id=chunk["folder_id"],
                    folder_name=chunk["folder_name"],
                    chunk_text=chunk["chunk_text"],
                    relevance_score=chunk["similarity_score"],
                    metadata=chunk["metadata"]
                )
                sources.append(source)
            
            processing_time = time.time() - start_time
            
            return RAGResponse(
                query=rag_query.query,
                answer=answer,
                sources=sources,
                total_chunks=len(similar_chunks),
                processing_time=processing_time
            )
            
        except Exception as e:
            if isinstance(e, (BadRequestException, PermissionDeniedException)):
                raise
            raise BadRequestException(f"Failed to process RAG query: {str(e)}")
    
    def _get_accessible_folders(
        self,
        user_id: UUID,
        requested_folder_ids: Optional[List[UUID]] = None
    ) -> List[UUID]:
        """Get list of folder IDs that user can access"""
        # Get all accessible folders for user
        accessible_folders = self.permission_service.get_user_accessible_folders(user_id)
        accessible_folder_ids = [folder.id for folder in accessible_folders]
        
        # If specific folders were requested, filter to only include accessible ones
        if requested_folder_ids:
            filtered_folder_ids = []
            for folder_id in requested_folder_ids:
                if folder_id in accessible_folder_ids:
                    filtered_folder_ids.append(folder_id)
            return filtered_folder_ids
        
        return accessible_folder_ids
    
    async def _generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """Generate answer using OpenAI with provided context"""
        # Prepare context from chunks
        context_texts = []
        for chunk in context_chunks:
            context_texts.append(
                f"Document: {chunk['document_name']}\n"
                f"Content: {chunk['chunk_text']}\n"
                f"Relevance: {chunk['similarity_score']:.2f}\n"
            )
        
        context = "\n---\n".join(context_texts)
        
        # Create prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on provided documents. 
Use only the information from the provided context to answer questions. 
If the context doesn't contain enough information to answer the question, say so clearly.
Cite the relevant documents when possible."""
        
        user_prompt = f"""Based on the following context documents, please answer this question: {query}

Context:
{context}

Answer:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise BadRequestException(f"Failed to generate answer: {str(e)}")
    
    def get_queryable_folders(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get list of folders that user can query"""
        accessible_folders = self.permission_service.get_user_accessible_folders(user_id)
        
        result = []
        for folder in accessible_folders:
            # Count documents in folder
            from app.models import Document
            document_count = self.db.query(Document).filter(
                Document.folder_id == folder.id
            ).count()
            
            # Count embeddings in folder
            from app.models import Embedding
            embedding_count = self.db.query(Embedding).join(Document).filter(
                Document.folder_id == folder.id
            ).count()
            
            result.append({
                "id": folder.id,
                "name": folder.name,
                "path": folder.path,
                "document_count": document_count,
                "embedding_count": embedding_count,
                "can_query": embedding_count > 0
            })
        
        return result
    
    async def suggest_related_queries(
        self,
        user_id: UUID,
        original_query: str,
        folder_ids: Optional[List[UUID]] = None
    ) -> List[str]:
        """Suggest related queries based on available content"""
        try:
            accessible_folders = self._get_accessible_folders(user_id, folder_ids)
            
            if not accessible_folders:
                return []
            
            # Get a sample of document titles and chunk texts for context
            from app.models import Document, Embedding
            
            # Get recent documents in accessible folders
            recent_docs = self.db.query(Document).filter(
                Document.folder_id.in_(accessible_folders)
            ).limit(10).all()
            
            doc_titles = [doc.filename for doc in recent_docs]
            
            # Create prompt for suggesting related queries
            system_prompt = """You are a helpful assistant that suggests related questions based on available documents.
Generate 3-5 related questions that someone might ask about the given documents."""
            
            user_prompt = f"""Based on these available documents: {', '.join(doc_titles)}
And the original query: "{original_query}"

Suggest 3-5 related questions that someone might ask:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            
            # Parse suggestions (assuming they're in a numbered list)
            suggestions = []
            for line in suggestions_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering and clean up
                    suggestion = line.split('.', 1)[-1].strip()
                    suggestion = suggestion.lstrip('- ').strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            # Return empty list on error rather than failing
            return []