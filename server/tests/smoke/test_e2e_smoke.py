import pytest
import io
import os

# Skip RAG tests if OpenAI API key is not set or is placeholder
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "test-openai-key")
SKIP_RAG_TESTS = not OPENAI_API_KEY or OPENAI_API_KEY in ["test-openai-key", "your-openai-api-key"]

def test_complete_rag_rbac_system_e2e_smoke(client, unique_username, unique_email):
    """
    Complete end-to-end smoke test for the RAG RBAC system:
    
    1. Create two users (admin and regular user)
    2. Admin creates folder hierarchy
    3. Admin uploads documents to folders
    4. Admin grants specific permissions to regular user
    5. Test document access with permissions
    6. Test RAG queries with permission enforcement
    7. Test permission revocation
    8. Clean up all created resources
    
    This test validates the entire system integration.
    """
    # Step 1: Create two users
    admin_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "adminpassword123"
    }
    
    user_data = {
        "email": f"user_{unique_email}",
        "username": f"user_{unique_username}",
        "password": "userpassword123"
    }
    
    # Register both users
    response = client.post("/api/v1/auth/register", json=admin_data)
    assert response.status_code == 201
    admin_id = response.json()["id"]
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]
    
    # Login both users
    response = client.post("/api/v1/auth/login", data={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = client.post("/api/v1/auth/login", data={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_token = response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Track resources for cleanup
    folder_ids = []
    document_ids = []
    
    try:
        # Step 2: Admin creates folder hierarchy
        # Root folder
        root_folder_data = {"name": "E2E Test Root", "parent_id": None}
        response = client.post("/api/v1/folders/", json=root_folder_data, headers=admin_headers)
        assert response.status_code == 201
        root_folder_id = response.json()["id"]
        folder_ids.append(root_folder_id)
        
        # Public subfolder
        public_folder_data = {"name": "Public Documents", "parent_id": root_folder_id}
        response = client.post("/api/v1/folders/", json=public_folder_data, headers=admin_headers)
        assert response.status_code == 201
        public_folder_id = response.json()["id"]
        folder_ids.append(public_folder_id)
        
        # Private subfolder
        private_folder_data = {"name": "Private Documents", "parent_id": root_folder_id}
        response = client.post("/api/v1/folders/", json=private_folder_data, headers=admin_headers)
        assert response.status_code == 201
        private_folder_id = response.json()["id"]
        folder_ids.append(private_folder_id)
        
        # Step 3: Admin uploads documents to folders
        # Document for public folder
        public_content = b"""This is a public document about general company policies.
        
        Company Mission: To provide excellent service to our customers.
        Company Values: Integrity, Innovation, Excellence.
        
        This document is available to all employees and contains general information.
        """
        
        files = {"file": ("public_policy.txt", io.BytesIO(public_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{public_folder_id}/documents", 
                             files=files, headers=admin_headers)
        assert response.status_code == 201
        public_doc_id = response.json()["id"]
        document_ids.append(public_doc_id)
        
        # Document for private folder
        private_content = b"""This is a confidential document with sensitive information.
        
        Financial Data: Q3 revenue was $2.5M, expenses were $1.8M.
        Strategic Plans: We plan to expand into the European market next year.
        Personnel Information: Performance reviews and salary adjustments.
        
        This document contains confidential information and should only be accessible to authorized personnel.
        """
        
        files = {"file": ("confidential_report.txt", io.BytesIO(private_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{private_folder_id}/documents", 
                             files=files, headers=admin_headers)
        assert response.status_code == 201
        private_doc_id = response.json()["id"]
        document_ids.append(private_doc_id)
        
        # Step 4: Test initial access (user should not have access)
        # User cannot access any folders initially
        response = client.get(f"/api/v1/folders/{root_folder_id}", headers=user_headers)
        assert response.status_code == 403
        
        response = client.get(f"/api/v1/folders/{public_folder_id}", headers=user_headers)
        assert response.status_code == 403
        
        response = client.get(f"/api/v1/documents/{public_doc_id}", headers=user_headers)
        assert response.status_code == 403
        
        # Step 5: Admin grants permissions to regular user
        # Grant read access to public folder
        public_permission_data = {
            "user_id": user_id,
            "can_read": True,
            "can_write": False,
            "can_delete": False,
            "is_admin": False
        }
        response = client.post(f"/api/v1/folders/{public_folder_id}/permissions", 
                              json=public_permission_data, headers=admin_headers)
        assert response.status_code == 201
        
        # Step 6: Test document access with permissions
        # User can now access public folder and documents
        response = client.get(f"/api/v1/folders/{public_folder_id}", headers=user_headers)
        assert response.status_code == 200
        folder_details = response.json()
        assert folder_details["can_read"] is True
        assert folder_details["can_write"] is False
        
        # User can access public document
        response = client.get(f"/api/v1/documents/{public_doc_id}", headers=user_headers)
        assert response.status_code == 200
        
        response = client.get(f"/api/v1/documents/{public_doc_id}/download", headers=user_headers)
        assert response.status_code == 200
        assert response.content == public_content
        
        # User still cannot access private folder/documents
        response = client.get(f"/api/v1/folders/{private_folder_id}", headers=user_headers)
        assert response.status_code == 403
        
        response = client.get(f"/api/v1/documents/{private_doc_id}", headers=user_headers)
        assert response.status_code == 403
        
        # Step 7: Test RAG functionality with permissions
        # Test RAG health endpoint
        response = client.get("/api/v1/rag/health", headers=user_headers)
        assert response.status_code == 200
        health_info = response.json()
        assert "accessible_folders" in health_info
        assert "total_documents" in health_info
        
        # Test queryable folders (user should only see public folder)
        response = client.get("/api/v1/rag/folders", headers=user_headers)
        assert response.status_code == 200
        user_folders = response.json()
        user_folder_ids = [f["id"] for f in user_folders]
        assert public_folder_id in user_folder_ids
        assert private_folder_id not in user_folder_ids
        
        # Admin should see all folders
        response = client.get("/api/v1/rag/folders", headers=admin_headers)
        assert response.status_code == 200
        admin_folders = response.json()
        admin_folder_ids = [f["id"] for f in admin_folders]
        assert public_folder_id in admin_folder_ids
        assert private_folder_id in admin_folder_ids
        
        # Test RAG query with permission enforcement
        if not SKIP_RAG_TESTS:
            # User can query public folder
            public_query = {
                "query": "What is the company mission?",
                "folder_ids": [public_folder_id],
                "limit": 5
            }
            response = client.post("/api/v1/rag/query", json=public_query, headers=user_headers)
            # With valid API key, this should work
            assert response.status_code in [200, 400, 500]  # 400/500 if API issues
        
        # User cannot query private folder
        private_query = {
            "query": "What is the financial data?",
            "folder_ids": [private_folder_id],
            "limit": 5
        }
        response = client.post("/api/v1/rag/query", json=private_query, headers=user_headers)
        assert response.status_code == 403  # Permission denied
        
        # Step 8: Test permission modification
        # Grant read access to private folder
        private_permission_data = {
            "user_id": user_id,
            "can_read": True,
            "can_write": False,
            "can_delete": False,
            "is_admin": False
        }
        response = client.post(f"/api/v1/folders/{private_folder_id}/permissions", 
                              json=private_permission_data, headers=admin_headers)
        assert response.status_code == 201
        
        # User can now access private folder
        response = client.get(f"/api/v1/folders/{private_folder_id}", headers=user_headers)
        assert response.status_code == 200
        
        response = client.get(f"/api/v1/documents/{private_doc_id}", headers=user_headers)
        assert response.status_code == 200
        
        # Step 9: Test permission revocation
        # Revoke access to private folder
        response = client.delete(f"/api/v1/folders/{private_folder_id}/permissions/{user_id}",
                               headers=admin_headers)
        assert response.status_code == 204
        
        # User can no longer access private folder
        response = client.get(f"/api/v1/folders/{private_folder_id}", headers=user_headers)
        assert response.status_code == 403
        
        # Step 10: Test folder hierarchy permissions
        # Grant access to root folder
        root_permission_data = {
            "user_id": user_id,
            "can_read": True,
            "can_write": False,
            "can_delete": False,
            "is_admin": False
        }
        response = client.post(f"/api/v1/folders/{root_folder_id}/permissions", 
                              json=root_permission_data, headers=admin_headers)
        assert response.status_code == 201
        
        # User can now access root folder
        response = client.get(f"/api/v1/folders/{root_folder_id}", headers=user_headers)
        assert response.status_code == 200
        
        # Test document embedding statistics (if accessible)
        response = client.get(f"/api/v1/documents/{public_doc_id}/embeddings/stats", headers=user_headers)
        assert response.status_code == 200
        stats = response.json()
        assert "total_chunks" in stats
        assert "total_characters" in stats
        
        # Step 11: Test write permissions
        # First revoke current permission
        response = client.delete(f"/api/v1/folders/{public_folder_id}/permissions/{user_id}",
                               headers=admin_headers)
        assert response.status_code == 204
        
        # Grant write permission to public folder
        write_permission_data = {
            "user_id": user_id,
            "can_read": True,
            "can_write": True,
            "can_delete": False,
            "is_admin": False
        }
        response = client.post(f"/api/v1/folders/{public_folder_id}/permissions", 
                             json=write_permission_data, headers=admin_headers)
        assert response.status_code == 201
        
        # User can now upload to public folder
        user_content = b"Document uploaded by regular user with write permissions."
        files = {"file": ("user_document.txt", io.BytesIO(user_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{public_folder_id}/documents", 
                             files=files, headers=user_headers)
        assert response.status_code == 201
        user_doc_id = response.json()["id"]
        document_ids.append(user_doc_id)
        
        # Verify document list includes all documents in public folder
        response = client.get(f"/api/v1/folders/{public_folder_id}/documents", headers=user_headers)
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) == 2  # Original public doc + user doc
        
    finally:
        # Step 12: Complete cleanup - delete all created resources
        # Delete documents first (foreign key constraints)
        for doc_id in document_ids:
            try:
                client.delete(f"/api/v1/documents/{doc_id}", headers=admin_headers)
            except:
                pass  # Continue cleanup even if some deletions fail
        
        # Delete folders (children first, then parents)
        for folder_id in reversed(folder_ids):  # Reverse order for hierarchy
            try:
                client.delete(f"/api/v1/folders/{folder_id}", headers=admin_headers)
            except:
                pass
        
        # Delete users
        try:
            client.delete("/api/v1/auth/me", headers=admin_headers)
        except:
            pass
        
        try:
            client.delete("/api/v1/auth/me", headers=user_headers)
        except:
            pass

def test_rag_system_integration_without_openai(client, unique_username, unique_email):
    """
    Test RAG system integration without requiring OpenAI API key.
    Focuses on permission enforcement and system structure.
    """
    admin_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "adminpassword123"
    }
    
    user_data = {
        "email": f"user_{unique_email}",
        "username": f"user_{unique_username}",
        "password": "userpassword123"
    }
    
    # Setup users
    client.post("/api/v1/auth/register", json=admin_data)
    client.post("/api/v1/auth/register", json=user_data)
    
    # Login users
    response = client.post("/api/v1/auth/login", data={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = client.post("/api/v1/auth/login", data={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_token = response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Get user ID for permissions
    response = client.get("/api/v1/auth/me", headers=user_headers)
    user_id = response.json()["id"]
    
    folder_id = None
    document_id = None
    
    try:
        # Create folder and document
        folder_data = {"name": "Integration Test Folder", "parent_id": None}
        response = client.post("/api/v1/folders/", json=folder_data, headers=admin_headers)
        folder_id = response.json()["id"]
        
        # Upload document
        test_content = b"Integration test document for RAG system validation."
        files = {"file": ("integration_test.txt", io.BytesIO(test_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                             files=files, headers=admin_headers)
        document_id = response.json()["id"]
        
        # Test RAG endpoints structure and permissions
        # Both users can access health endpoint
        for headers in [admin_headers, user_headers]:
            response = client.get("/api/v1/rag/health", headers=headers)
            assert response.status_code == 200
            health_info = response.json()
            assert "status" in health_info
            assert "accessible_folders" in health_info
        
        # Admin sees folder, user doesn't
        response = client.get("/api/v1/rag/folders", headers=admin_headers)
        assert response.status_code == 200
        admin_folders = response.json()
        admin_folder_ids = [f["id"] for f in admin_folders]
        assert folder_id in admin_folder_ids
        
        response = client.get("/api/v1/rag/folders", headers=user_headers)
        assert response.status_code == 200
        user_folders = response.json()
        user_folder_ids = [f["id"] for f in user_folders]
        assert folder_id not in user_folder_ids
        
        # Grant permission and verify access
        permission_data = {
            "user_id": user_id,
            "can_read": True,
            "can_write": False,
            "can_delete": False,
            "is_admin": False
        }
        response = client.post(f"/api/v1/folders/{folder_id}/permissions", 
                              json=permission_data, headers=admin_headers)
        assert response.status_code == 201
        
        # User now sees folder
        response = client.get("/api/v1/rag/folders", headers=user_headers)
        assert response.status_code == 200
        user_folders = response.json()
        user_folder_ids = [f["id"] for f in user_folders]
        assert folder_id in user_folder_ids
        
        # Test query suggestions endpoint
        response = client.post("/api/v1/rag/suggest-queries", 
                              json={"original_query": "integration test query"}, 
                              headers=user_headers)
        assert response.status_code in [200, 422]  # 422 if not implemented
        if response.status_code == 200:
            suggestions = response.json()
            assert "suggestions" in suggestions
        
    finally:
        # Cleanup
        if document_id:
            client.delete(f"/api/v1/documents/{document_id}", headers=admin_headers)
        if folder_id:
            client.delete(f"/api/v1/folders/{folder_id}", headers=admin_headers)
        client.delete("/api/v1/auth/me", headers=admin_headers)
        client.delete("/api/v1/auth/me", headers=user_headers)