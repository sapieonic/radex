"""
Unit tests for RAG schemas.
Tests validation, serialization, and data models.
"""
import pytest
from pydantic import ValidationError
from uuid import uuid4
from app.schemas.rag import (
    RAGQuery,
    RAGChunk,
    RAGResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingStatus
)


class TestRAGQuery:
    """Test RAGQuery schema validation"""

    def test_valid_rag_query(self):
        """Test valid RAG query creation"""
        folder_id = uuid4()
        query = RAGQuery(
            query="What is the main topic?",
            folder_ids=[folder_id],
            limit=10,
            min_relevance_score=0.7
        )
        assert query.query == "What is the main topic?"
        assert query.folder_ids == [folder_id]
        assert query.limit == 10
        assert query.min_relevance_score == 0.7

    def test_rag_query_defaults(self):
        """Test RAG query with default values"""
        query = RAGQuery(query="Test query")
        assert query.folder_ids is None
        assert query.limit == 10
        assert query.min_relevance_score == 0.7

    def test_rag_query_empty_string(self):
        """Test RAG query rejects empty string"""
        with pytest.raises(ValidationError):
            RAGQuery(query="")

    def test_rag_query_limit_validation(self):
        """Test limit validation (1-50)"""
        # Valid limits
        RAGQuery(query="test", limit=1)
        RAGQuery(query="test", limit=50)

        # Invalid limits
        with pytest.raises(ValidationError):
            RAGQuery(query="test", limit=0)
        with pytest.raises(ValidationError):
            RAGQuery(query="test", limit=51)

    def test_rag_query_relevance_score_validation(self):
        """Test relevance score validation (0.0-1.0)"""
        # Valid scores
        RAGQuery(query="test", min_relevance_score=0.0)
        RAGQuery(query="test", min_relevance_score=1.0)

        # Invalid scores
        with pytest.raises(ValidationError):
            RAGQuery(query="test", min_relevance_score=-0.1)
        with pytest.raises(ValidationError):
            RAGQuery(query="test", min_relevance_score=1.1)


class TestRAGChunk:
    """Test RAGChunk schema"""

    def test_valid_rag_chunk(self):
        """Test valid RAG chunk creation"""
        doc_id = uuid4()
        folder_id = uuid4()
        chunk = RAGChunk(
            document_id=doc_id,
            document_name="test.pdf",
            folder_id=folder_id,
            folder_name="Test Folder",
            chunk_text="Sample chunk text",
            relevance_score=0.85,
            metadata={"page": 1}
        )
        assert chunk.document_id == doc_id
        assert chunk.relevance_score == 0.85
        assert chunk.metadata == {"page": 1}


class TestRAGResponse:
    """Test RAGResponse schema"""

    def test_valid_rag_response(self):
        """Test valid RAG response creation"""
        doc_id = uuid4()
        folder_id = uuid4()
        chunks = [
            RAGChunk(
                document_id=doc_id,
                document_name="test.pdf",
                folder_id=folder_id,
                folder_name="Test Folder",
                chunk_text="Sample text",
                relevance_score=0.9
            )
        ]
        response = RAGResponse(
            query="What is this?",
            answer="This is a test.",
            sources=chunks,
            total_chunks=1,
            processing_time=0.5
        )
        assert response.query == "What is this?"
        assert response.answer == "This is a test."
        assert len(response.sources) == 1
        assert response.processing_time == 0.5


class TestChatMessage:
    """Test ChatMessage schema"""

    def test_valid_user_message(self):
        """Test valid user message"""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_valid_assistant_message(self):
        """Test valid assistant message"""
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"

    def test_valid_system_message(self):
        """Test valid system message"""
        msg = ChatMessage(role="system", content="You are a helpful assistant")
        assert msg.role == "system"

    def test_invalid_role(self):
        """Test invalid role is rejected"""
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid", content="test")

    def test_empty_content(self):
        """Test empty content is rejected"""
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="")

    def test_long_content(self):
        """Test very long content (10000 char limit)"""
        long_content = "a" * 10000
        msg = ChatMessage(role="user", content=long_content)
        assert len(msg.content) == 10000

        # Test exceeding limit
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="a" * 10001)


class TestChatRequest:
    """Test ChatRequest schema"""

    def test_valid_chat_request(self):
        """Test valid chat request"""
        folder_id = uuid4()
        messages = [
            ChatMessage(role="user", content="What is RAG?"),
            ChatMessage(role="assistant", content="RAG stands for Retrieval Augmented Generation.")
        ]
        request = ChatRequest(
            messages=messages,
            folder_ids=[folder_id],
            limit=5
        )
        assert len(request.messages) == 2
        assert len(request.folder_ids) == 1
        assert request.limit == 5

    def test_chat_request_defaults(self):
        """Test chat request with defaults"""
        folder_id = uuid4()
        messages = [ChatMessage(role="user", content="Test")]
        request = ChatRequest(messages=messages, folder_ids=[folder_id])
        assert request.limit == 10
        assert request.min_relevance_score == 0.7

    def test_empty_messages(self):
        """Test empty messages list is rejected"""
        folder_id = uuid4()
        with pytest.raises(ValidationError):
            ChatRequest(messages=[], folder_ids=[folder_id])

    def test_empty_folders(self):
        """Test empty folder list is rejected"""
        messages = [ChatMessage(role="user", content="Test")]
        with pytest.raises(ValidationError):
            ChatRequest(messages=messages, folder_ids=[])

    def test_max_messages_validation(self):
        """Test max messages limit (100)"""
        folder_id = uuid4()
        messages = [ChatMessage(role="user", content=f"Message {i}") for i in range(100)]
        request = ChatRequest(messages=messages, folder_ids=[folder_id])
        assert len(request.messages) == 100

        # Test exceeding limit
        messages_too_many = [ChatMessage(role="user", content=f"Message {i}") for i in range(101)]
        with pytest.raises(ValidationError):
            ChatRequest(messages=messages_too_many, folder_ids=[folder_id])


class TestChatResponse:
    """Test ChatResponse schema"""

    def test_valid_chat_response(self):
        """Test valid chat response"""
        doc_id = uuid4()
        folder_id = uuid4()
        sources = [
            RAGChunk(
                document_id=doc_id,
                document_name="test.pdf",
                folder_id=folder_id,
                folder_name="Test Folder",
                chunk_text="Sample text",
                relevance_score=0.9
            )
        ]
        response = ChatResponse(
            role="assistant",
            content="Here is the answer",
            sources=sources,
            total_chunks=1,
            processing_time=1.2,
            reformulated_query="What is the reformulated question?"
        )
        assert response.role == "assistant"
        assert response.content == "Here is the answer"
        assert len(response.sources) == 1
        assert response.reformulated_query == "What is the reformulated question?"

    def test_chat_response_without_reformulated_query(self):
        """Test chat response without reformulated query"""
        response = ChatResponse(
            role="assistant",
            content="Answer",
            sources=[],
            total_chunks=0,
            processing_time=0.5
        )
        assert response.reformulated_query is None


class TestEmbeddingStatus:
    """Test EmbeddingStatus schema"""

    def test_valid_embedding_status(self):
        """Test valid embedding status"""
        doc_id = uuid4()
        status = EmbeddingStatus(
            document_id=doc_id,
            status="completed",
            total_chunks=10,
            processed_chunks=10
        )
        assert status.status == "completed"
        assert status.total_chunks == 10
        assert status.processed_chunks == 10

    def test_embedding_status_with_error(self):
        """Test embedding status with error"""
        doc_id = uuid4()
        status = EmbeddingStatus(
            document_id=doc_id,
            status="failed",
            error_message="Processing failed"
        )
        assert status.status == "failed"
        assert status.error_message == "Processing failed"
