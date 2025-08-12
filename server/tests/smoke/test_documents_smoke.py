import pytest
import tempfile
import io

def test_document_lifecycle_smoke(client, unique_username, unique_email):
    """
    Smoke test for complete document lifecycle:
    1. Create user
    2. Create folder
    3. Upload document
    4. List documents in folder
    5. Get document metadata
    6. Download document
    7. Delete document
    8. Clean up folder and user
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
    folder_data = {"name": "Document Test Folder", "parent_id": None}
    response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
    folder_id = response.json()["id"]
    
    document_id = None
    
    try:
        # Step 3: Upload document
        test_content = b"This is a test document for smoke testing.\nIt contains multiple lines for testing."
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(test_content)
            tmp_file.flush()
            
            with open(tmp_file.name, "rb") as f:
                files = {"file": ("test_document.txt", f, "text/plain")}
                response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                                     files=files, headers=headers)
        
        assert response.status_code == 201
        upload_response = response.json()
        assert upload_response["filename"] == "test_document.txt"
        assert upload_response["file_type"] == "txt"
        assert upload_response["folder_id"] == folder_id
        assert "id" in upload_response
        document_id = upload_response["id"]
        
        # Step 4: List documents in folder
        response = client.get(f"/api/v1/folders/{folder_id}/documents", headers=headers)
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) == 1
        assert documents[0]["id"] == document_id
        assert documents[0]["filename"] == "test_document.txt"
        
        # Step 5: Get document metadata
        response = client.get(f"/api/v1/documents/{document_id}", headers=headers)
        assert response.status_code == 200
        doc_metadata = response.json()
        assert doc_metadata["id"] == document_id
        assert doc_metadata["filename"] == "test_document.txt"
        assert doc_metadata["file_type"] == "txt"
        assert doc_metadata["folder_id"] == folder_id
        
        # Step 6: Download document
        response = client.get(f"/api/v1/documents/{document_id}/download", headers=headers)
        assert response.status_code == 200
        assert response.content == test_content
        
        # Step 7: Delete document
        response = client.delete(f"/api/v1/documents/{document_id}", headers=headers)
        assert response.status_code == 204
        document_id = None  # Mark as deleted
        
        # Verify document is deleted
        response = client.get(f"/api/v1/folders/{folder_id}/documents", headers=headers)
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) == 0
        
    finally:
        # Clean up
        if document_id:
            client.delete(f"/api/v1/documents/{document_id}", headers=headers)
        client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        client.delete("/api/v1/auth/me", headers=headers)

def test_document_upload_different_file_types(client, unique_username, unique_email):
    """Test uploading different file types"""
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
    folder_data = {"name": "Multi-type Test Folder", "parent_id": None}
    response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
    folder_id = response.json()["id"]
    
    document_ids = []
    
    try:
        # Test different file types
        file_tests = [
            ("test.txt", b"Text file content", "text/plain"),
            ("test.md", b"# Markdown content\nThis is markdown", "text/markdown"),
            ("test.html", b"<html><body><h1>HTML content</h1></body></html>", "text/html"),
        ]
        
        for filename, content, content_type in file_tests:
            files = {"file": (filename, io.BytesIO(content), content_type)}
            response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                                 files=files, headers=headers)
            assert response.status_code == 201
            upload_response = response.json()
            assert upload_response["filename"] == filename
            document_ids.append(upload_response["id"])
        
        # Verify all documents are listed
        response = client.get(f"/api/v1/folders/{folder_id}/documents", headers=headers)
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) == 3
        
    finally:
        # Clean up all documents
        for doc_id in document_ids:
            client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
        client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        client.delete("/api/v1/auth/me", headers=headers)

def test_document_permission_enforcement(client, unique_username, unique_email):
    """Test that document access respects folder permissions"""
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
    
    # Get user2 ID for permissions
    response = client.get("/api/v1/auth/me", headers=user2_headers)
    user2_id = response.json()["id"]
    
    folder_id = None
    document_id = None
    
    try:
        # User1 creates folder and uploads document
        folder_data = {"name": "Permission Test Folder", "parent_id": None}
        response = client.post("/api/v1/folders/", json=folder_data, headers=user1_headers)
        folder_id = response.json()["id"]
        
        # Upload document
        test_content = b"Private document content"
        files = {"file": ("private.txt", io.BytesIO(test_content), "text/plain")}
        response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                             files=files, headers=user1_headers)
        assert response.status_code == 201
        document_id = response.json()["id"]
        
        # User2 cannot access document initially
        response = client.get(f"/api/v1/documents/{document_id}", headers=user2_headers)
        assert response.status_code == 403
        
        response = client.get(f"/api/v1/documents/{document_id}/download", headers=user2_headers)
        assert response.status_code == 403
        
        # Grant read permission to user2
        permission_data = {
            "user_id": user2_id,
            "can_read": True,
            "can_write": False,
            "can_delete": False,
            "is_admin": False
        }
        response = client.post(f"/api/v1/folders/{folder_id}/permissions", 
                              json=permission_data, headers=user1_headers)
        assert response.status_code == 201
        
        # User2 can now read document
        response = client.get(f"/api/v1/documents/{document_id}", headers=user2_headers)
        assert response.status_code == 200
        
        response = client.get(f"/api/v1/documents/{document_id}/download", headers=user2_headers)
        assert response.status_code == 200
        assert response.content == test_content
        
        # User2 still cannot delete document (no delete permission)
        response = client.delete(f"/api/v1/documents/{document_id}", headers=user2_headers)
        assert response.status_code == 403
        
    finally:
        # Clean up
        if document_id:
            client.delete(f"/api/v1/documents/{document_id}", headers=user1_headers)
        if folder_id:
            client.delete(f"/api/v1/folders/{folder_id}", headers=user1_headers)
        client.delete("/api/v1/auth/me", headers=user1_headers)
        client.delete("/api/v1/auth/me", headers=user2_headers)

def test_document_duplicate_filename_same_folder_fails(client, unique_username, unique_email):
    """Test that duplicate filenames in same folder fail"""
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
    folder_data = {"name": "Duplicate Test Folder", "parent_id": None}
    response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
    folder_id = response.json()["id"]
    
    document_id = None
    
    try:
        # Upload first document
        content1 = b"First document content"
        files = {"file": ("duplicate.txt", io.BytesIO(content1), "text/plain")}
        response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                             files=files, headers=headers)
        assert response.status_code == 201
        document_id = response.json()["id"]
        
        # Try to upload second document with same filename
        content2 = b"Second document content"
        files = {"file": ("duplicate.txt", io.BytesIO(content2), "text/plain")}
        response = client.post(f"/api/v1/folders/{folder_id}/documents", 
                             files=files, headers=headers)
        assert response.status_code == 400  # Bad request
        
    finally:
        # Clean up
        if document_id:
            client.delete(f"/api/v1/documents/{document_id}", headers=headers)
        client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        client.delete("/api/v1/auth/me", headers=headers)