import pytest
import tempfile
import uuid
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    """Create test client for smoke tests using the live application"""
    # Use the live application without database overrides for smoke tests
    # This ensures we're testing against the actual running services
    return TestClient(app)

@pytest.fixture
def test_file():
    """Create a temporary test file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(b"This is a test document for smoke testing.\nIt contains multiple lines.\nFor testing text extraction.")
        tmp.flush()
        yield tmp.name
    
    # Cleanup is handled by the file being temporary

@pytest.fixture
def test_pdf_content():
    """Mock PDF content for testing"""
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n164\n%%EOF"

@pytest.fixture
def unique_username():
    """Generate a unique username for tests"""
    return f"testuser_{uuid.uuid4().hex[:8]}"

@pytest.fixture
def unique_email():
    """Generate a unique email for tests"""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"