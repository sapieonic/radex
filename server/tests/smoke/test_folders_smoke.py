import pytest
import uuid

def test_folder_crud_lifecycle_smoke(client, unique_username, unique_email):
    """
    Smoke test for complete folder lifecycle:
    1. Create user
    2. Create folder
    3. List folders
    4. Get folder details
    5. Update folder
    6. Create subfolder
    7. Delete subfolder
    8. Delete main folder
    9. Clean up user
    """
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    # Step 1: Create user and get auth
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    folder_id = None
    subfolder_id = None
    
    try:
        # Step 2: Create folder
        folder_data = {
            "name": "Test Documents",
            "parent_id": None
        }
        response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
        assert response.status_code == 201
        folder_response = response.json()
        assert folder_response["name"] == folder_data["name"]
        assert folder_response["parent_id"] is None
        assert "id" in folder_response
        assert folder_response["path"] == "/Test Documents"
        folder_id = folder_response["id"]
        
        # Step 3: List folders
        response = client.get("/api/v1/folders/", headers=headers)
        assert response.status_code == 200
        folders = response.json()
        assert len(folders) == 1
        assert folders[0]["id"] == folder_id
        assert folders[0]["can_read"] is True
        assert folders[0]["can_write"] is True
        assert folders[0]["can_delete"] is True
        assert folders[0]["is_admin"] is True
        
        # Step 4: Get folder details
        response = client.get(f"/api/v1/folders/{folder_id}", headers=headers)
        assert response.status_code == 200
        folder_details = response.json()
        assert folder_details["id"] == folder_id
        assert folder_details["name"] == "Test Documents"
        
        # Step 5: Update folder
        update_data = {"name": "Updated Test Documents"}
        response = client.put(f"/api/v1/folders/{folder_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        updated_folder = response.json()
        assert updated_folder["name"] == "Updated Test Documents"
        assert updated_folder["path"] == "/Updated Test Documents"
        
        # Step 6: Create subfolder
        subfolder_data = {
            "name": "Subfolder",
            "parent_id": folder_id
        }
        response = client.post("/api/v1/folders/", json=subfolder_data, headers=headers)
        assert response.status_code == 201
        subfolder_response = response.json()
        assert subfolder_response["name"] == "Subfolder"
        assert subfolder_response["parent_id"] == folder_id
        assert subfolder_response["path"] == "/Updated Test Documents/Subfolder"
        subfolder_id = subfolder_response["id"]
        
        # Verify folder list now shows 2 folders
        response = client.get("/api/v1/folders/", headers=headers)
        assert response.status_code == 200
        folders = response.json()
        assert len(folders) == 2
        
        # Step 7: Delete subfolder
        response = client.delete(f"/api/v1/folders/{subfolder_id}", headers=headers)
        assert response.status_code == 204
        subfolder_id = None  # Mark as deleted
        
        # Verify folder list now shows 1 folder again
        response = client.get("/api/v1/folders/", headers=headers)
        assert response.status_code == 200
        folders = response.json()
        assert len(folders) == 1
        
        # Step 8: Delete main folder
        response = client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        assert response.status_code == 204
        folder_id = None  # Mark as deleted
        
        # Verify no folders remain
        response = client.get("/api/v1/folders/", headers=headers)
        assert response.status_code == 200
        folders = response.json()
        assert len(folders) == 0
        
    finally:
        # Clean up any remaining folders
        if subfolder_id:
            client.delete(f"/api/v1/folders/{subfolder_id}", headers=headers)
        if folder_id:
            client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        
        # Step 9: Clean up user
        client.delete("/api/v1/auth/me", headers=headers)

def test_folder_permissions_smoke(client, unique_username, unique_email):
    """
    Smoke test for folder permissions:
    1. Create two users
    2. User1 creates folder
    3. User1 grants permission to User2
    4. User2 can access folder
    5. User1 revokes permission
    6. User2 cannot access folder
    7. Clean up
    """
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
    
    # Get user1 info to get user ID
    response = client.get("/api/v1/auth/me", headers=user1_headers)
    user1_id = response.json()["id"]
    
    response = client.post("/api/v1/auth/login", data={
        "username": user2_data["username"],
        "password": user2_data["password"]
    })
    user2_token = response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # Get user2 info to get user ID
    response = client.get("/api/v1/auth/me", headers=user2_headers)
    user2_id = response.json()["id"]
    
    folder_id = None
    
    try:
        # User1 creates folder
        folder_data = {"name": "Shared Folder", "parent_id": None}
        response = client.post("/api/v1/folders/", json=folder_data, headers=user1_headers)
        assert response.status_code == 201
        folder_id = response.json()["id"]
        
        # User2 cannot access folder initially
        response = client.get(f"/api/v1/folders/{folder_id}", headers=user2_headers)
        assert response.status_code == 403
        
        # User1 grants read permission to User2
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
        
        # User2 can now access folder
        response = client.get(f"/api/v1/folders/{folder_id}", headers=user2_headers)
        assert response.status_code == 200
        folder_details = response.json()
        assert folder_details["can_read"] is True
        assert folder_details["can_write"] is False
        assert folder_details["can_delete"] is False
        assert folder_details["is_admin"] is False
        
        # User1 revokes permission
        response = client.delete(f"/api/v1/folders/{folder_id}/permissions/{user2_id}",
                               headers=user1_headers)
        assert response.status_code == 204
        
        # User2 cannot access folder anymore
        response = client.get(f"/api/v1/folders/{folder_id}", headers=user2_headers)
        assert response.status_code == 403
        
    finally:
        # Clean up
        if folder_id:
            client.delete(f"/api/v1/folders/{folder_id}", headers=user1_headers)
        client.delete("/api/v1/auth/me", headers=user1_headers)
        client.delete("/api/v1/auth/me", headers=user2_headers)

def test_folder_duplicate_name_same_parent_fails(client, unique_username, unique_email):
    """Test that duplicate folder names in same parent fail"""
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
    
    folder_id = None
    
    try:
        # Create first folder
        folder_data = {"name": "Duplicate Name", "parent_id": None}
        response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
        assert response.status_code == 201
        folder_id = response.json()["id"]
        
        # Try to create second folder with same name and parent
        response = client.post("/api/v1/folders/", json=folder_data, headers=headers)
        assert response.status_code == 409  # Conflict
        
    finally:
        # Clean up
        if folder_id:
            client.delete(f"/api/v1/folders/{folder_id}", headers=headers)
        client.delete("/api/v1/auth/me", headers=headers)