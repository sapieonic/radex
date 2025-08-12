import pytest
import uuid

def test_user_registration_login_deletion_smoke(client, unique_username, unique_email):
    """
    Smoke test for complete user lifecycle:
    1. Register user
    2. Login user  
    3. Get user info
    4. Delete user
    5. Verify user is deleted
    """
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    # Step 1: Register user
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    user_response = response.json()
    assert user_response["email"] == user_data["email"]
    assert user_response["username"] == user_data["username"]
    assert user_response["is_active"] is True
    assert "id" in user_response
    user_id = user_response["id"]
    
    # Step 2: Login user
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    login_response = response.json()
    assert "access_token" in login_response
    assert login_response["token_type"] == "bearer"
    
    token = login_response["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Get user info
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["id"] == user_id
    assert user_info["email"] == user_data["email"]
    assert user_info["username"] == user_data["username"]
    
    # Step 4: Delete user
    response = client.delete("/api/v1/auth/me", headers=headers)
    assert response.status_code == 204
    
    # Step 5: Verify user is deleted - token should no longer work
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401  # Unauthorized

def test_user_registration_duplicate_email(client, unique_username):
    """Test that duplicate email registration fails"""
    email = "duplicate@example.com"
    
    user_data_1 = {
        "email": email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    user_data_2 = {
        "email": email,
        "username": f"{unique_username}_2",
        "password": "testpassword456"
    }
    
    # First registration should succeed
    response = client.post("/api/v1/auth/register", json=user_data_1)
    assert response.status_code == 201
    
    try:
        # Second registration with same email should fail
        response = client.post("/api/v1/auth/register", json=user_data_2)
        assert response.status_code == 409  # Conflict
        
    finally:
        # Clean up - delete first user
        login_data = {
            "username": user_data_1["username"],
            "password": user_data_1["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            client.delete("/api/v1/auth/me", headers=headers)

def test_user_registration_duplicate_username(client, unique_email):
    """Test that duplicate username registration fails"""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    
    user_data_1 = {
        "email": unique_email,
        "username": username,
        "password": "testpassword123"
    }
    
    user_data_2 = {
        "email": f"another_{unique_email}",
        "username": username,
        "password": "testpassword456"
    }
    
    # First registration should succeed
    response = client.post("/api/v1/auth/register", json=user_data_1)
    assert response.status_code == 201
    
    try:
        # Second registration with same username should fail
        response = client.post("/api/v1/auth/register", json=user_data_2)
        assert response.status_code == 409  # Conflict
        
    finally:
        # Clean up - delete first user
        login_data = {
            "username": user_data_1["username"],
            "password": user_data_1["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            client.delete("/api/v1/auth/me", headers=headers)

def test_invalid_login_credentials(client):
    """Test login with invalid credentials"""
    # Test with non-existent user
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401

def test_token_refresh(client, unique_username, unique_email):
    """Test token refresh functionality"""
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword123"
    }
    
    # Register and login
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test token refresh
        response = client.post("/api/v1/auth/refresh", headers=headers)
        assert response.status_code == 200
        refresh_response = response.json()
        assert "access_token" in refresh_response
        assert refresh_response["token_type"] == "bearer"
        # Note: Token might be the same if generated at the same time, but should be valid
        new_token = refresh_response["access_token"]
        
        # Verify new token works by making an authenticated request
        new_headers = {"Authorization": f"Bearer {new_token}"}
        response = client.get("/api/v1/auth/me", headers=new_headers)
        assert response.status_code == 200
        
    finally:
        # Clean up
        client.delete("/api/v1/auth/me", headers=headers)