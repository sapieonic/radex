"""
Unit test fixtures and configuration.
Unit tests should be fast, isolated, and not require external dependencies.
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app.models import User, Folder, Document, Permission

# In-memory SQLite for fast unit tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def mock_db() -> Mock:
    """Mock database session for unit tests"""
    mock = Mock(spec=Session)
    mock.query = Mock()
    mock.add = Mock()
    mock.commit = Mock()
    mock.refresh = Mock()
    mock.delete = Mock()
    mock.flush = Mock()
    return mock


@pytest.fixture(scope="function")
def in_memory_db():
    """In-memory database for unit tests requiring real DB"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock = MagicMock()
    mock.chat.completions.create = MagicMock()
    mock.embeddings.create = MagicMock()
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = MagicMock()
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock()
    mock.delete = MagicMock()
    return mock


@pytest.fixture
def mock_minio():
    """Mock MinIO client"""
    mock = MagicMock()
    mock.bucket_exists = MagicMock(return_value=True)
    mock.put_object = MagicMock()
    mock.get_object = MagicMock()
    mock.remove_object = MagicMock()
    return mock


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewgF5W9rVq8uUWsS",
        is_active=True,
        is_superuser=False
    )
    return user


@pytest.fixture
def sample_admin_user():
    """Sample admin user for testing"""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="admin@example.com",
        username="admin",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewgF5W9rVq8uUWsS",
        is_active=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def sample_folder(sample_user):
    """Sample folder for testing"""
    from uuid import uuid4
    folder = Folder(
        id=uuid4(),
        name="Test Folder",
        path="/Test Folder",
        owner_id=sample_user.id,
        parent_id=None
    )
    return folder


@pytest.fixture
def sample_document(sample_folder):
    """Sample document for testing"""
    from uuid import uuid4
    document = Document(
        id=uuid4(),
        filename="test.pdf",
        original_filename="test.pdf",
        file_path="test/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        folder_id=sample_folder.id,
        status="completed"
    )
    return document


@pytest.fixture
def sample_permission(sample_user, sample_folder):
    """Sample permission for testing"""
    from uuid import uuid4
    permission = Permission(
        id=uuid4(),
        user_id=sample_user.id,
        folder_id=sample_folder.id,
        can_read=True,
        can_write=False,
        can_delete=False,
        is_admin=False
    )
    return permission
