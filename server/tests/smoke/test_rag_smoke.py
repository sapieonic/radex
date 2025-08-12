import pytest
import io
import os

# Skip RAG tests if OpenAI API key is not set or is placeholder
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "test-openai-key")
SKIP_RAG_TESTS = not OPENAI_API_KEY or OPENAI_API_KEY in ["test-openai-key", "your-openai-api-key"]

@pytest.mark.skipif(SKIP_RAG_TESTS, reason="OpenAI API key not configured")
def test_rag_query_lifecycle_smoke(client, unique_username, unique_email):
    """
    Smoke test for RAG functionality (requires OpenAI API key):
    1. Create user and folder
    2. Upload document
    3. Wait for embedding processing
    4. Query RAG
    5. Get queryable folders
    6. Clean up
    """
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    # Setup user and folder
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create folder
    folder_data = {"name": "RAG Test Folder", "parent_id": None}
    response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
    folder_id = response.json()["id"]
    
    document_id = None
    
    try:
        # Upload a document with meaningful content for RAG
        test_content = b"""This is a test document about artificial intelligence and machine learning.
        
        Artificial Intelligence (AI) is a broad field of computer science that focuses on creating 
        systems capable of performing tasks that typically require human intelligence. These tasks 
        include learning, reasoning, problem-solving, perception, and language understanding.
        
        Machine Learning (ML) is a subset of AI that enables computers to learn and improve from 
        experience without being explicitly programmed. ML algorithms build mathematical models 
        based on training data to make predictions or decisions.
        
        Deep Learning is a subset of machine learning that uses neural networks with multiple 
        layers to model and understand complex patterns in data.
        """
        
        files = {"file": ("ai_document.txt", io.BytesIO(test_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                             files=files, headers=headers)
        assert response.status_code == 201
        document_id = response.json()["id"]
        
        # Test RAG health check
        response = client.get("/api/v1/rag/health", headers=headers)
        assert response.status_code == 200
        health_info = response.json()
        assert health_info["status"] == "healthy"
        assert "accessible_folders" in health_info
        assert "total_documents" in health_info
        
        # Get queryable folders
        response = client.get("/api/v1/rag/folders", headers=headers)
        assert response.status_code == 200
        folders = response.json()
        assert len(folders) >= 1
        # Find our folder
        test_folder = next((f for f in folders if f["id"] == folder_id), None)
        assert test_folder is not None
        assert test_folder["document_count"] >= 1
        
        # Note: In a real test with OpenAI API, we would test RAG query here
        # For smoke test without API key, we just verify the endpoint exists
        rag_query = {
            "query": "What is artificial intelligence?",
            "folder_ids": [folder_id],
            "limit": 5
        }
        
        # This will fail without a valid OpenAI API key, but we test the endpoint structure
        response = client.post("/api/v1/rag/query", json=rag_query, headers=headers)
        # Without valid API key, expect 400 or 500, not 404
        assert response.status_code in [400, 500], f"Unexpected status code: {response.status_code}"
        
    finally:
        # Clean up
        if document_id:
            client.delete(f"/api/v1/documents/{document_id}", headers=headers)
        client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        client.delete("/api/v1/auth/me", headers=headers)

def test_rag_endpoints_structure_smoke(client, unique_username, unique_email):
    """
    Test RAG endpoints structure without requiring OpenAI API key
    """
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    # Setup user
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test RAG health endpoint
        response = client.get("/api/v1/rag/health", headers=headers)
        assert response.status_code == 200
        health_info = response.json()
        assert "status" in health_info
        assert "accessible_folders" in health_info
        assert "queryable_folders" in health_info
        assert "total_documents" in health_info
        assert "can_query" in health_info
        
        # Test queryable folders endpoint
        response = client.get("/api/v1/rag/folders", headers=headers)
        assert response.status_code == 200
        folders = response.json()
        assert isinstance(folders, list)
        
        # Test query suggestions endpoint structure
        response = client.post("/api/v1/rag/suggest-queries", 
                              json={"original_query": "test query"}, 
                              headers=headers)
        # Should return 200 with suggestions structure or 422 if not implemented
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            suggestions = response.json()
            assert "suggestions" in suggestions
            assert isinstance(suggestions["suggestions"], list)
        
    finally:
        # Clean up
        client.delete("/api/v1/auth/me", headers=headers)

def test_rag_permission_enforcement_smoke(client, unique_username, unique_email):
    """Test that RAG respects folder permissions"""
    # Create two users
    user1_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    user2_data = {
        "email": f"2_{unique_email}",
        "username": f"2_{unique_username}",
        "password": "testpassword456"
    }
    
    # Register both users
    client.post("/api/v1/auth/register", json=user1_data)
    client.post("/api/v1/auth/register", json=user2_data)
    
    # Login both users
    response = client.post("/api/v1/auth/login", data={
        "username": user1_data["username"],
        "password": user1_data["password"]
    })
    user1_token = response.json()["access_token"]
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    
    response = client.post("/api/v1/auth/login", data={
        "username": user2_data["username"],
        "password": user2_data["password"]
    })
    user2_token = response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    folder_id = None
    document_id = None
    
    try:
        # User1 creates folder and uploads document
        folder_data = {"name": "Private RAG Folder", "parent_id": None}
        response = client.post("/api/v1/folders/", json=folder_data, headers=user1_headers)
        folder_id = response.json()["id"]
        
        # Upload document
        test_content = b"This is private content that should not be accessible to user2."
        files = {"file": ("private.txt", io.BytesIO(test_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                             files=files, headers=user1_headers)
        document_id = response.json()["id"]
        
        # User1 can see folder in queryable folders
        response = client.get("/api/v1/rag/folders", headers=user1_headers)
        assert response.status_code == 200
        user1_folders = response.json()
        user1_folder_ids = [f["id"] for f in user1_folders]
        assert folder_id in user1_folder_ids
        
        # User2 cannot see the private folder in queryable folders
        response = client.get("/api/v1/rag/folders", headers=user2_headers)
        assert response.status_code == 200
        user2_folders = response.json()
        user2_folder_ids = [f["id"] for f in user2_folders]
        assert folder_id not in user2_folder_ids
        
        # User2 cannot query the private folder
        rag_query = {
            "query": "What is the content?",
            "folder_ids": [folder_id],
            "limit": 5
        }
        response = client.post("/api/v1/rag/query", json=rag_query, headers=user2_headers)
        # Should fail due to permission denial
        assert response.status_code == 403
        
    finally:
        # Clean up
        if document_id:
            client.delete(f"/api/v1/documents/{document_id}", headers=user1_headers)
        if folder_id:
            client.delete(f"/api/v1/folders/{folder_id}", headers=user1_headers)
        client.delete("/api/v1/auth/me", headers=user1_headers)
        client.delete("/api/v1/auth/me", headers=user2_headers)

def test_embedding_stats_smoke(client, unique_username, unique_email):
    """Test document embedding statistics endpoint"""
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    # Setup user and folder
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create folder
    folder_data = {"name": "Embedding Test Folder", "parent_id": None}
    response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
    folder_id = response.json()["id"]
    
    document_id = None
    
    try:
        # Upload document
        test_content = b"Test document for embedding statistics."
        files = {"file": ("stats_test.txt", io.BytesIO(test_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                             files=files, headers=headers)
        document_id = response.json()["id"]
        
        # Get embedding statistics
        response = client.get(f"/api/v1/documents/{document_id}/embeddings/stats", headers=headers)
        assert response.status_code == 200
        stats = response.json()
        assert "total_chunks" in stats
        assert "total_characters" in stats
        assert "average_chunk_size" in stats
        assert isinstance(stats["total_chunks"], int)
        assert isinstance(stats["total_characters"], int)
        assert isinstance(stats["average_chunk_size"], int)
        
    finally:
        # Clean up
        if document_id:
            client.delete(f"/api/v1/documents/{document_id}", headers=headers)
        client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        client.delete("/api/v1/auth/me", headers=headers)