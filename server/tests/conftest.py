import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.config import Settings

# Test database URL - use SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    # Clean up
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_settings():
    """Test settings"""
    return Settings(
        database_url=TEST_DATABASE_URL,
        redis_url="redis://localhost:6379/1",  # Use different DB for tests
        minio_endpoint="localhost:9000",
        minio_access_key="minioadmin",
        minio_secret_key="minioadmin",
        minio_bucket="test-documents",
        jwt_secret_key="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expiration_minutes=30,
        openai_api_key="test-openai-key",
        app_name="RAG RBAC Test",
        debug=True
    )

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }

@pytest.fixture
def another_test_user_data():
    """Another test user data"""
    return {
        "email": "test2@example.com", 
        "username": "testuser2",
        "password": "testpassword456"
    }

@pytest.fixture
def test_folder_data():
    """Test folder data"""
    return {
        "name": "Test Documents",
        "parent_id": None
    }

@pytest.fixture
def test_document_content():
    """Test document content"""
    return b"This is a test document content for testing purposes."

@pytest.fixture
def cleanup_files():
    """Cleanup any test files created during tests"""
    created_files = []
    
    def _add_file(filepath):
        created_files.append(filepath)
    
    yield _add_file
    
    # Cleanup
    for filepath in created_files:
        if os.path.exists(filepath):
            os.remove(filepath)