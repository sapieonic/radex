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
from app.schemas import RAGQuery, RAGResponse, RAGChunk, ChatRequest, ChatResponse, ChatMessage

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
                model=settings.openai_chat_model,
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
                model=settings.openai_chat_model,
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

    async def _reformulate_query(
        self,
        messages: List[ChatMessage],
        max_history: int = 5
    ) -> str:
        """
        Reformulate the latest user query based on conversation history.
        Takes last N messages for context and generates a standalone query.
        Falls back to original query if reformulation fails.
        """
        # Extract the latest user message
        user_messages = [msg for msg in messages if msg.role == "user"]
        if not user_messages:
            raise BadRequestException("No user messages found in conversation history")

        latest_query = user_messages[-1].content

        # If this is the first message or only one message, no reformulation needed
        if len(messages) <= 1:
            return latest_query

        # Take last N messages for context (excluding the latest)
        context_messages = messages[-(max_history + 1):-1] if len(messages) > max_history else messages[:-1]

        try:
            # Build context from conversation history
            conversation_context = "\n".join([
                f"{msg.role.upper()}: {msg.content}"
                for msg in context_messages
            ])

            system_prompt = """You are a query reformulation assistant. Your task is to reformulate user queries into standalone, self-contained questions based on conversation history.

Given a conversation history and the latest user query, reformulate the query to be completely standalone and contextually complete. The reformulated query should:
1. Include all necessary context from the conversation
2. Be understandable without reading the conversation history
3. Preserve the user's intent
4. Be suitable for semantic search over documents

Only return the reformulated query, nothing else."""

            user_prompt = f"""Conversation history:
{conversation_context}

Latest user query: {latest_query}

Reformulated standalone query:"""

            response = self.openai_client.chat.completions.create(
                model=settings.openai_reformulation_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.3  # Lower temperature for more consistent reformulation
            )

            reformulated = response.choices[0].message.content.strip()

            # Validate reformulation - if it's empty or too short, fall back
            if not reformulated or len(reformulated) < 5:
                return latest_query

            return reformulated

        except Exception as e:
            # Fall back to original query on any error
            print(f"Query reformulation failed: {str(e)}. Using original query.")
            return latest_query

    async def chat(
        self,
        user_id: UUID,
        chat_request: ChatRequest
    ) -> ChatResponse:
        """
        Process a chat request with conversation history.
        Uses last 5 messages for context and reformulates queries for better retrieval.
        """
        start_time = time.time()

        try:
            # Validate that we have messages
            if not chat_request.messages:
                raise BadRequestException("No messages provided in chat request")

            # Get accessible folders for the user
            accessible_folders = self._get_accessible_folders(user_id, chat_request.folder_ids)

            if not accessible_folders:
                raise PermissionDeniedException("No accessible folders found for query")

            # Take last 5 messages for context window
            context_window_size = 5
            recent_messages = chat_request.messages[-context_window_size:] if len(chat_request.messages) > context_window_size else chat_request.messages

            # Reformulate the latest query based on conversation history
            reformulated_query = await self._reformulate_query(recent_messages)

            # Generate query embedding using reformulated query
            query_embedding = self.embedding_service.generate_embeddings([reformulated_query])[0]

            # Search for similar chunks
            similar_chunks = self.embedding_service.search_similar_chunks(
                query_embedding=query_embedding,
                folder_ids=accessible_folders,
                limit=chat_request.limit,
                min_similarity=chat_request.min_relevance_score
            )

            if not similar_chunks:
                return ChatResponse(
                    role="assistant",
                    content="No relevant documents found for your query.",
                    sources=[],
                    total_chunks=0,
                    processing_time=time.time() - start_time,
                    reformulated_query=reformulated_query
                )

            # Generate answer using conversation context + retrieved documents
            answer = await self._generate_chat_answer(recent_messages, similar_chunks)

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

            return ChatResponse(
                role="assistant",
                content=answer,
                sources=sources,
                total_chunks=len(similar_chunks),
                processing_time=processing_time,
                reformulated_query=reformulated_query
            )

        except Exception as e:
            if isinstance(e, (BadRequestException, PermissionDeniedException)):
                raise
            raise BadRequestException(f"Failed to process chat request: {str(e)}")

    async def _generate_chat_answer(
        self,
        messages: List[ChatMessage],
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generate chat answer using conversation history and retrieved context.
        Uses the last N messages to maintain conversation continuity.
        """
        # Prepare context from chunks
        context_texts = []
        for chunk in context_chunks:
            context_texts.append(
                f"Document: {chunk['document_name']}\n"
                f"Content: {chunk['chunk_text']}\n"
                f"Relevance: {chunk['similarity_score']:.2f}\n"
            )

        document_context = "\n---\n".join(context_texts)

        # Create system prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on provided documents and conversation history.

Use the provided document context to answer questions accurately. Maintain conversation continuity by considering the chat history.
If the document context doesn't contain enough information to answer the question, say so clearly.
Cite the relevant documents when possible.
Be conversational and natural in your responses."""

        # Build messages for OpenAI
        openai_messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (excluding system messages from user)
        for msg in messages[:-1]:  # Exclude the last message initially
            if msg.role != "system":
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add the latest message with document context
        latest_message = messages[-1]
        if latest_message.role == "user":
            enhanced_content = f"""Based on the following document context, please answer this question:

Question: {latest_message.content}

Document Context:
{document_context}

Answer:"""
            openai_messages.append({
                "role": "user",
                "content": enhanced_content
            })

        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=openai_messages,
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise BadRequestException(f"Failed to generate chat answer: {str(e)}")