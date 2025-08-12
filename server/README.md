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

### 3. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **API Health Check**: http://localhost:8000/health

## API Usage Examples

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=securepassword123"
```

### 3. Create a Folder

```bash
curl -X POST "http://localhost:8000/api/v1/folders" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Documents",
    "parent_id": null
  }'
```

### 4. Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/folders/{folder_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/your/document.pdf"
```

### 5. Query with RAG

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

#### Prerequisites for Testing

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

#### Running All Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test files
pytest tests/test_auth.py
pytest tests/test_folders.py
```

#### Running Smoke Tests

The smoke tests validate the complete system integration and require the full environment to be running:

```bash
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

#### Test Environment Notes

- **Cleanup**: All smoke tests include automatic cleanup of created resources
- **Isolation**: Each test uses unique usernames/emails to avoid conflicts  
- **Permissions**: Tests validate RBAC functionality thoroughly
- **Error Handling**: Tests cover both success and failure scenarios
- **Integration**: E2E tests validate complete system workflows

#### Test Structure

```
tests/
├── conftest.py                    # Shared test fixtures
├── test_auth.py                   # Unit tests for authentication
├── test_folders.py                # Unit tests for folder management
├── smoke/                         # Integration smoke tests
│   ├── conftest.py               # Smoke test fixtures
│   ├── test_auth_smoke.py        # Authentication lifecycle tests
│   ├── test_folders_smoke.py     # Folder CRUD and permissions
│   ├── test_documents_smoke.py   # Document management tests
│   ├── test_rag_smoke.py         # RAG functionality tests
│   └── test_e2e_smoke.py         # Complete system integration tests
```

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