# RAG Solution with RBAC - Implementation Guide

## Project Structure

```
radex/
├── server/
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── folder.py
│   │   │   ├── document.py
│   │   │   ├── permission.py
│   │   │   └── embedding.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── folder.py
│   │   │   ├── document.py
│   │   │   └── rag.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── folders.py
│   │   │   ├── documents.py
│   │   │   └── rag.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── permission_service.py
│   │   │   └── rag_service.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── dependencies.py
│   │   │   └── exceptions.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_processing.py
│   │       └── text_chunking.py
│   └── tests/
└── client/  # Frontend (optional for now)
```

## Step 1: Environment Setup

### Create `.env.example` file:
```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=ragdb
DB_USER=raguser
DB_PASSWORD=changeme

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=changeme

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=documents

# JWT
JWT_SECRET_KEY=your-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Firebase (optional for now)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
```

### Create `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pgvector==0.2.3
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
minio==7.2.0
redis==5.0.1
celery==5.3.4
openai==1.3.7
pypdf==3.17.1
python-docx==1.1.0
beautifulsoup4==4.12.2
markdown==3.5.1
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      minio:
        condition: service_started
    volumes:
      - ./app:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

## Step 2: Database Setup

### Create `init.sql`:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Folders table
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, parent_id)
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    folder_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    file_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permissions table
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    can_read BOOLEAN DEFAULT false,
    can_write BOOLEAN DEFAULT false,
    can_delete BOOLEAN DEFAULT false,
    is_admin BOOLEAN DEFAULT false,
    granted_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, folder_id)
);

-- Embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- Indexes
CREATE INDEX idx_folders_parent ON folders(parent_id);
CREATE INDEX idx_folders_owner ON folders(owner_id);
CREATE INDEX idx_documents_folder ON documents(folder_id);
CREATE INDEX idx_permissions_user_folder ON permissions(user_id, folder_id);
CREATE INDEX idx_embeddings_document ON embeddings(document_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Step 3: Core Implementation

### 1. Create `app/config.py`:
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # MinIO
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "documents"
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # OpenAI
    openai_api_key: str
    
    # App
    app_name: str = "RAG RBAC System"
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Create `app/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3. Create SQLAlchemy Models in `app/models/`:
- Define User, Folder, Document, Permission, and Embedding models
- Use UUID for primary keys
- Implement relationships between models

### 4. Create Pydantic Schemas in `app/schemas/`:
- Request/response models for authentication
- Folder operations schemas
- Document upload/retrieval schemas
- RAG query schemas

### 5. Create Core Security in `app/core/security.py`:
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt
```

## Step 4: API Implementation

### Authentication Endpoints (`app/api/auth.py`):
1. **POST /register** - User registration
2. **POST /login** - User login with JWT token generation
3. **POST /refresh** - Token refresh
4. **GET /me** - Get current user info

### Folder Management Endpoints (`app/api/folders.py`):
1. **GET /folders** - List user's accessible folders
2. **POST /folders** - Create new folder
3. **GET /folders/{id}** - Get folder details
4. **PUT /folders/{id}** - Update folder
5. **DELETE /folders/{id}** - Delete folder (cascade delete documents)
6. **POST /folders/{id}/permissions** - Grant user permissions
7. **GET /folders/{id}/permissions** - List folder permissions

### Document Management Endpoints (`app/api/documents.py`):
1. **POST /folders/{folder_id}/documents** - Upload document
2. **GET /documents/{id}** - Download document
3. **DELETE /documents/{id}** - Delete document
4. **GET /documents/{id}/metadata** - Get document metadata

### RAG Endpoints (`app/api/rag.py`):
1. **POST /rag/query** - Submit RAG query
2. **GET /rag/folders** - List folders user can query

## Step 5: Services Implementation

### Authentication Service (`app/services/auth_service.py`):
- User registration with password hashing
- Login validation and token generation
- Token validation middleware
- Current user dependency injection

### Permission Service (`app/services/permission_service.py`):
- Check user permissions for folder/document
- Inherit permissions from parent folders
- Permission validation decorator
- Bulk permission checks for efficiency

### Document Service (`app/services/document_service.py`):
- File upload to MinIO
- File type validation
- Metadata extraction
- Document deletion with MinIO cleanup
- Trigger embedding generation on upload

### Embedding Service (`app/services/embedding_service.py`):
```python
import openai
from typing import List
import numpy as np

class EmbeddingService:
    def __init__(self):
        openai.api_key = settings.openai_api_key
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=texts
        )
        return [r.embedding for r in response.data]
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200):
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks
```

### RAG Service (`app/services/rag_service.py`):
```python
class RAGService:
    def __init__(self, db_session, embedding_service):
        self.db = db_session
        self.embedding_service = embedding_service
    
    async def query(self, user_id: str, query_text: str, folder_ids: List[str] = None):
        # 1. Check user permissions for folders
        accessible_folders = await self.get_accessible_folders(user_id, folder_ids)
        
        # 2. Generate query embedding
        query_embedding = self.embedding_service.generate_embeddings([query_text])[0]
        
        # 3. Vector similarity search with permission filter
        results = await self.vector_search(query_embedding, accessible_folders)
        
        # 4. Format and return results
        return self.format_results(results)
    
    async def vector_search(self, query_embedding, folder_ids, limit=10):
        # Use pgvector for similarity search
        query = """
            SELECT e.*, d.filename, d.folder_id,
                   e.embedding <=> %s::vector as distance
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
            WHERE d.folder_id = ANY(%s)
            ORDER BY distance
            LIMIT %s
        """
        return await self.db.execute(query, (query_embedding, folder_ids, limit))
```

## Step 6: File Processing Utils

### Create `app/utils/file_processing.py`:
```python
import PyPDF2
import docx
from bs4 import BeautifulSoup
import markdown

def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from various file formats"""
    if file_type == 'pdf':
        return extract_pdf_text(file_path)
    elif file_type in ['docx', 'doc']:
        return extract_docx_text(file_path)
    elif file_type == 'html':
        return extract_html_text(file_path)
    elif file_type == 'md':
        return extract_markdown_text(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def extract_pdf_text(file_path: str) -> str:
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text
```

## Step 7: Main Application

### Create `app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, folders, documents, rag
from app.database import engine
from app.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAG RBAC System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(folders.router, prefix="/api/v1/folders", tags=["folders"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

## Step 8: Background Tasks (Optional - for async processing)

### Create `app/tasks.py`:
```python
from celery import Celery
from app.config import settings

celery_app = Celery('tasks', broker=settings.redis_url)

@celery_app.task
def process_document(document_id: str):
    """Background task to process document and generate embeddings"""
    # 1. Fetch document from database
    # 2. Extract text from file
    # 3. Chunk text
    # 4. Generate embeddings
    # 5. Store embeddings in database
    pass
```

## Step 9: Testing

### Create basic tests in `tests/`:
```python
# tests/test_auth.py
def test_user_registration(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 201

def test_user_login(client):
    response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Step 10: Running the Application

### Development Setup:
```bash
# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d postgres redis minio

# Install dependencies
pip install -r requirements.txt

# Run migrations (if using Alembic)
alembic upgrade head

# Start application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup:
```bash
# Build and run all services
docker-compose up --build
```

## API Usage Examples

### 1. Register User:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user1","password":"pass123"}'
```

### 2. Login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=pass123"
```

### 3. Create Folder:
```bash
curl -X POST http://localhost:8000/api/v1/folders \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Documents","parent_id":null}'
```

### 4. Upload Document:
```bash
curl -X POST http://localhost:8000/api/v1/folders/{folder_id}/documents \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf"
```

### 5. RAG Query:
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the main topic?","folder_ids":["folder-uuid"]}'
```

## Key Implementation Notes

1. **Permission Checks**: Always validate permissions before any operation
2. **File Storage**: Use MinIO for actual file storage, store only metadata in PostgreSQL
3. **Embeddings**: Generate embeddings asynchronously after document upload
4. **Caching**: Use Redis to cache permission checks and frequently accessed data
5. **Error Handling**: Implement proper error responses with meaningful messages
6. **Logging**: Add logging for debugging and audit trails
7. **Pagination**: Implement pagination for list endpoints
8. **Validation**: Use Pydantic for request/response validation

## Simplified Security Approach

For faster development:
- Basic JWT authentication (no refresh tokens initially)
- Simple role-based permissions (owner has all permissions)
- No encryption at rest (add later if needed)
- Basic password requirements only
- CORS allow all origins for development

## Next Steps After Basic Implementation

1. Add more sophisticated text chunking strategies
2. Implement document versioning
3. Add batch document upload
4. Create admin panel
5. Add more file format support
6. Implement rate limiting
7. Add comprehensive logging
8. Create API documentation with Swagger
9. Build simple web UI
10. Add integration tests