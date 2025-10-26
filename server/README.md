# RAG Solution with Role-Based Access Control (RBAC)

A comprehensive Retrieval-Augmented Generation (RAG) solution with role-based access control, built with FastAPI, PostgreSQL, and OpenAI.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **Folder Management**: Hierarchical folder structure with granular permissions
- **Document Management**: Upload, process, and manage documents with text extraction
- **Vector Embeddings**: Automatic document processing and embedding generation using OpenAI
- **RAG Queries**: AI-powered question answering with source citations
- **Role-Based Access Control**: Fine-grained permissions at folder and document levels
- **File Storage**: MinIO S3-compatible object storage
- **Scalable Architecture**: Containerized deployment with Docker

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API Key

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# IMPORTANT: Set your OpenAI API key and change JWT secret
```

### 2. Start Services

```bash
# Start all services with Docker Compose
docker-compose up --build

# Or start infrastructure only (for development)
docker-compose up -d postgres redis minio
```

### 3. Create Admin User

The system includes a default admin user that's automatically created during database initialization:

**Default Admin Credentials:**
- **Username**: `admin`
- **Password**: `admin123456`
- **Email**: `admin@example.com`

#### Alternative: Create Admin User Manually

If you need to create additional admin users or the default admin doesn't exist, use the provided script:

```bash
# Option 1: Use the interactive script
./create_superuser.sh

# Option 2: Create directly via SQL (if using Docker)
docker exec -i server-postgres-1 psql -U raguser -d ragdb << 'EOF'
INSERT INTO users (email, username, hashed_password, is_active, is_superuser) 
VALUES (
    'admin@example.com', 
    'admin', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewgF5W9rVq8uUWsS',
    true, 
    true
) ON CONFLICT (email) DO NOTHING;
EOF

# Option 3: Use the Python script
python create_admin_user.py
```

#### Admin User Capabilities

Admin users (superusers) have full system access including:
- View and manage all folders regardless of ownership
- Grant/revoke permissions on any folder to any user  
- Create, update, and delete any user account
- Access all admin-only API endpoints
- View system-wide statistics and logs

**⚠️ Security Note**: Change the default admin password immediately in production environments.

### 4. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **API Health Check**: http://localhost:8000/health

## API Usage Examples

### 1. Admin Login

```bash
# Login as admin user
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123456"
```

### 2. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### 3. Regular User Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=securepassword123"
```

### 4. Create a Folder

```bash
curl -X POST "http://localhost:8000/api/v1/folders" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Documents",
    "parent_id": null
  }'
```

### 5. Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/folders/{folder_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/your/document.pdf"
```

### 6. Find a User (for sharing)

```bash
# Find user by email
curl -X GET "http://localhost:8000/api/v1/users/find?email=user@example.com" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Find user by username
curl -X GET "http://localhost:8000/api/v1/users/find?username=testuser" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Admin: Create a User

```bash
# Admin users can create other users with any privileges
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "securepassword123",
    "is_active": true,
    "is_superuser": false
  }'
```

### 8. Query with RAG

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic of the documents?",
    "folder_ids": ["folder-uuid"],
    "limit": 5
  }'
```

## Project Structure

```
server/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Security, dependencies, exceptions
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic services
│   ├── utils/         # Utilities (file processing, text chunking)
│   ├── config.py      # Configuration settings
│   ├── database.py    # Database connection
│   └── main.py        # FastAPI application
├── tests/             # Test files
├── docker-compose.yml # Docker services
├── Dockerfile         # Application container
├── requirements.txt   # Python dependencies
├── init.sql          # Database initialization
└── .env.example      # Environment template
```

## Supported File Types

- **PDF**: `.pdf`
- **Word Documents**: `.docx`, `.doc`
- **Text Files**: `.txt`
- **Markdown**: `.md`
- **HTML**: `.html`, `.htm`

## Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://raguser:changeme@postgres:5432/ragdb

# Redis
REDIS_URL=redis://:changeme@redis:6379/0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# JWT
JWT_SECRET_KEY=your-secret-key-change-this
JWT_EXPIRATION_MINUTES=30

# OpenAI
OPENAI_API_KEY=your-openai-api-key
```

## Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start infrastructure services
docker-compose up -d postgres redis minio

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

The project includes comprehensive test coverage with both unit tests and integration smoke tests.

#### Test Structure

```
tests/
├── unit/                          # Unit tests (isolated, fast)
│   ├── conftest.py               # Unit test fixtures and mocks
│   ├── api/                      # API endpoint tests
│   │   └── test_auth.py         # Authentication endpoints
│   ├── core/                     # Core functionality tests
│   │   └── test_security.py     # Password hashing, JWT tokens
│   ├── schemas/                  # Pydantic schema validation tests
│   │   └── test_rag.py          # RAG request/response schemas
│   ├── services/                 # Business logic tests
│   │   └── test_permission_service.py  # RBAC permission logic
│   └── utils/                    # Utility function tests
│       └── test_text_chunking.py # Text processing utilities
└── smoke/                         # Integration smoke tests
    ├── conftest.py               # Smoke test fixtures
    ├── test_auth_smoke.py        # Authentication lifecycle tests
    ├── test_folders_smoke.py     # Folder CRUD and permissions
    ├── test_documents_smoke.py   # Document management tests
    ├── test_rag_smoke.py         # RAG functionality tests
    └── test_e2e_smoke.py         # Complete system integration tests
```

#### Running Unit Tests

Unit tests are fast, isolated tests that don't require external services. They use mocking to test business logic independently.

```bash
# Set up Python environment
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all unit tests
pytest tests/unit/ -v

# Run with coverage report
pytest tests/unit/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/core/test_security.py -v

# Run specific test class or method
pytest tests/unit/services/test_permission_service.py::TestCheckFolderPermission -v
```

**Unit Test Coverage:**
- 99 unit tests covering core functionality
- API endpoints, authentication, and authorization
- Password hashing and JWT token generation
- RAG schema validation
- Permission checking and RBAC logic
- Text chunking and processing utilities

**Coverage Goals:**
- Overall coverage: 80%+
- New code coverage: 90%+
- Critical paths: 100%

#### Prerequisites for Integration Testing

1. **Start the development services:**
   ```bash
   # Start infrastructure services
   docker-compose -f dev-docker-compose.yml up -d

   # Or start all services including postgres, redis, minio
   docker-compose up -d postgres redis minio
   ```

2. **Set up Python environment:**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   pip install pytest pytest-asyncio httpx
   ```

3. **Start the FastAPI server:**
   ```bash
   # In a separate terminal with venv activated
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Running Integration Tests

```bash
# Run all tests (unit + smoke)
pytest tests/

# Run all smoke tests
pytest tests/smoke/ -v

# Run specific smoke test categories
pytest tests/smoke/test_auth_smoke.py -v          # Authentication lifecycle
pytest tests/smoke/test_folders_smoke.py -v      # Folder CRUD and permissions
pytest tests/smoke/test_documents_smoke.py -v    # Document management
pytest tests/smoke/test_rag_smoke.py -v          # RAG functionality
pytest tests/smoke/test_e2e_smoke.py -v          # End-to-end integration

# Run smoke tests with cleanup verification
pytest tests/smoke/ -v --tb=short
```

#### RAG Tests with OpenAI

For full RAG functionality testing, set your OpenAI API key:

```bash
# Set OpenAI API key for RAG tests
export OPENAI_API_KEY="your-actual-openai-api-key"

# Run RAG tests (these will be skipped without a valid API key)
pytest tests/smoke/test_rag_smoke.py -v
pytest tests/smoke/test_e2e_smoke.py::test_complete_rag_rbac_system_e2e_smoke -v
```

#### Continuous Integration

Unit tests run automatically on every push and pull request via GitHub Actions:

```yaml
# See .github/workflows/unit-tests.yml
- Runs on: ubuntu-latest
- Python version: 3.11
- Coverage reporting included
- No external dependencies required
```

#### Test Environment Notes

**Unit Tests:**
- No external services required (database, Redis, MinIO)
- Use mocking for all external dependencies
- Fast execution (< 3 seconds for all 99 tests)
- Run in CI/CD pipeline on every commit
- Coverage reports generated automatically

**Smoke Tests:**
- **Cleanup**: All smoke tests include automatic cleanup of created resources
- **Isolation**: Each test uses unique usernames/emails to avoid conflicts
- **Permissions**: Tests validate RBAC functionality thoroughly
- **Error Handling**: Tests cover both success and failure scenarios
- **Integration**: E2E tests validate complete system workflows

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt password hashing
- **Role-Based Access Control**: Granular folder and document permissions
- **Input Validation**: Pydantic schema validation
- **File Size Limits**: Configurable upload limits
- **Permission Inheritance**: Hierarchical permission model

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/auth/refresh` - Refresh token

### Folders
- `GET /api/v1/folders` - List accessible folders
- `POST /api/v1/folders` - Create folder
- `GET /api/v1/folders/{id}` - Get folder details
- `PUT /api/v1/folders/{id}` - Update folder
- `DELETE /api/v1/folders/{id}` - Delete folder
- `POST /api/v1/folders/{id}/permissions` - Grant permissions
- `GET /api/v1/folders/{id}/permissions` - List permissions

### Documents
- `POST /api/v1/folders/{folder_id}/documents` - Upload document
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents/{id}/download` - Download document
- `DELETE /api/v1/documents/{id}` - Delete document
- `GET /api/v1/folders/{folder_id}/documents` - List folder documents

### Users
- `GET /api/v1/users/find` - Find user by email/username (all users)
- `GET /api/v1/users/` - List users with filters (admin only)
- `GET /api/v1/users/search` - Search users (admin only) 
- `GET /api/v1/users/{id}` - Get user by ID (admin only)
- `POST /api/v1/users/` - Create user (admin only)
- `PUT /api/v1/users/{id}` - Update user (admin only)
- `DELETE /api/v1/users/{id}` - Delete user (admin only)

### RAG
- `POST /api/v1/rag/query` - Submit RAG query
- `GET /api/v1/rag/folders` - List queryable folders
- `POST /api/v1/rag/suggest-queries` - Get query suggestions
- `GET /api/v1/rag/health` - RAG system health

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.