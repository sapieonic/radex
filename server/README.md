# RAG Solution with Role-Based Access Control (RBAC)

A comprehensive Retrieval-Augmented Generation (RAG) solution with role-based access control, built with FastAPI, PostgreSQL, and OpenAI.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **Folder Management**: Hierarchical folder structure with granular permissions
- **Document Management**: Upload, process, and manage documents with text extraction
- **Vector Embeddings**: Automatic document processing and embedding generation using OpenAI
- **RAG Queries**: AI-powered question answering with source citations
- **Role-Based Access Control**: Fine-grained permissions at folder and document levels
- **Confluence Integration**: Import and sync content from Confluence Cloud/Server/Data Center
- **File Storage**: MinIO S3-compatible object storage
- **Background Processing**: Celery-based async tasks for large imports
- **Scalable Architecture**: Containerized deployment with Docker

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API Key
- (Optional) Confluence API Token or OAuth credentials for Confluence integration

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

### 9. Confluence Integration

#### Add Confluence Credentials
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/auth" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confluence_type": "cloud",
    "base_url": "https://yourcompany.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "your-confluence-api-token"
  }'
```

#### List Confluence Spaces
```bash
curl -X GET "http://localhost:8000/api/v1/confluence/spaces?credential_id=CREDENTIAL_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Import Confluence Space
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "CREDENTIAL_ID",
    "folder_id": "FOLDER_ID",
    "import_type": "space",
    "space_key": "SPACE_KEY",
    "include_attachments": true
  }'
```

#### Check Import Status
```bash
curl -X GET "http://localhost:8000/api/v1/confluence/import/IMPORT_ID/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Project Structure

```
server/
├── app/
│   ├── api/           # API endpoints
│   │   └── confluence.py  # Confluence integration endpoints
│   ├── core/          # Security, dependencies, exceptions
│   ├── models/        # SQLAlchemy models
│   │   ├── confluence_credential.py
│   │   ├── confluence_import.py
│   │   └── confluence_page.py
│   ├── schemas/       # Pydantic schemas
│   │   └── confluence.py
│   ├── services/      # Business logic services
│   │   └── confluence/    # Confluence integration services
│   │       ├── auth_service.py
│   │       ├── client.py
│   │       ├── extractor.py
│   │       └── import_service.py
│   ├── workers/       # Background task workers
│   │   ├── confluence_import.py
│   │   └── confluence_sync.py
│   ├── utils/         # Utilities (file processing, text chunking)
│   ├── config.py      # Configuration settings
│   ├── database.py    # Database connection
│   └── main.py        # FastAPI application
├── tests/             # Test files
├── docker-compose.yml # Docker services
├── Dockerfile         # Application container
├── requirements.txt   # Python dependencies
├── init.sql          # Database initialization
├── .env.example      # Environment template
├── .env.confluence.example  # Confluence config example
├── CONFLUENCE_TESTING.md    # Confluence API testing guide
└── README.md         # This file
```

## Supported Content Sources

### File Types
- **PDF**: `.pdf`
- **Word Documents**: `.docx`, `.doc`
- **Text Files**: `.txt`
- **Markdown**: `.md`
- **HTML**: `.html`, `.htm`

### Confluence Integration
- **Confluence Cloud**: OAuth 2.0 authentication
- **Confluence Server/Data Center**: API token authentication
- **Content Types**: Pages, spaces, page trees, attachments
- **Format Conversion**: Automatic HTML to Markdown conversion with macro handling
- **Synchronization**: Manual and scheduled content synchronization

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

# Confluence Integration (optional)
CONFLUENCE_OAUTH_CLIENT_ID=your-oauth-client-id
CONFLUENCE_OAUTH_CLIENT_SECRET=your-oauth-client-secret
CONFLUENCE_ENCRYPTION_KEY=your-encryption-key-32-bytes
CONFLUENCE_MAX_IMPORT_SIZE=100
CONFLUENCE_RATE_LIMIT=10
CONFLUENCE_SYNC_INTERVAL=3600

# Celery (for background tasks)
CELERY_BROKER_URL=redis://:changeme@redis:6379/1
CELERY_RESULT_BACKEND=redis://:changeme@redis:6379/1
```

## Confluence Integration Setup

### Getting Confluence Credentials

#### For Confluence Cloud
1. **API Token Method** (Recommended):
   - Go to [Atlassian Account Security](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Click "Create API token"
   - Label it (e.g., "RADEX RAG Integration")
   - Copy the generated token
   - Use with your Atlassian email address

2. **OAuth Method** (Advanced):
   - Create an OAuth app in [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
   - Configure OAuth 2.0 with appropriate scopes
   - Set redirect URI to `http://localhost:8000/api/v1/confluence/oauth/callback`
   - Add client ID and secret to your .env file

#### For Confluence Server/Data Center
1. Generate a Personal Access Token or API token from your Confluence admin
2. Use your Confluence email and the API token

### Setting up Confluence Integration

1. **Configure Environment Variables**:
   ```bash
   # Copy the example configuration
   cp .env.confluence.example .env.confluence
   
   # Add to your main .env file
   cat .env.confluence >> .env
   ```

2. **Start Celery Workers** (for background imports):
   ```bash
   # Start Celery worker for background tasks
   celery -A app.workers.confluence_import worker --loglevel=info
   
   # Start Celery Beat for scheduled tasks (optional)
   celery -A app.workers.confluence_sync beat --loglevel=info
   ```

3. **Test the Integration**:
   - Follow the examples in `CONFLUENCE_TESTING.md`
   - Use the API docs at `http://localhost:8000/docs`
   - Check import status and logs

### Confluence Integration Features

- **Content Import**: Import individual pages, entire spaces, or page hierarchies
- **Attachment Support**: Import and process file attachments
- **Content Conversion**: Automatic HTML to Markdown conversion with Confluence macro handling
- **Incremental Sync**: Detect and sync only changed content
- **Background Processing**: Large imports run asynchronously with progress tracking
- **Permission Integration**: Imported content respects the existing RBAC system
- **Search Integration**: Imported Confluence content is searchable via RAG queries

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

### Confluence Integration
- `POST /api/v1/confluence/auth` - Add/update Confluence credentials
- `GET /api/v1/confluence/auth` - List user's Confluence credentials
- `DELETE /api/v1/confluence/auth/{id}` - Delete Confluence credentials
- `GET /api/v1/confluence/spaces` - List Confluence spaces
- `GET /api/v1/confluence/spaces/{key}/pages` - List pages in a space
- `POST /api/v1/confluence/search` - Search Confluence content
- `POST /api/v1/confluence/import` - Create import job
- `POST /api/v1/confluence/import/batch` - Batch import multiple items
- `GET /api/v1/confluence/import/{id}/status` - Check import status
- `POST /api/v1/confluence/sync/{id}` - Manual sync of imported content
- `GET /api/v1/confluence/sync/history` - Get sync history

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.