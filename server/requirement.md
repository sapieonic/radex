# Technical Requirements Document: RAG Solution with Role-Based Access Control (RBAC)

## 1. Executive Summary

This document outlines the technical requirements for building a Retrieval-Augmented Generation (RAG) solution with Role-Based Access Control (RBAC) capabilities. The system will allow users to organize documents in folders with strict access controls, ensuring content isolation between different user groups while providing RAG functionality within authorized boundaries.

## 2. System Overview

### 2.1 Core Features
- **Folder-based Document Organization**: Hierarchical folder structure for document management
- **Role-Based Access Control**: Granular permissions at folder and document levels
- **Document Ingestion Pipeline**: Automated processing and vectorization of uploaded documents
- **Secure RAG Operations**: Context-aware retrieval respecting access permissions
- **Containerized Deployment**: Cloud-agnostic solution using Docker containers

### 2.2 Key Components
- **Authentication & Authorization Service**
- **Document Management Service**
- **Vector Store (PostgreSQL with pgvector)**
- **Ingestion Pipeline**
- **RAG Engine**
- **API Gateway**
- **Web Interface**

## 3. Functional Requirements

### 3.1 User Management
- User registration and authentication
- Role assignment and management
- Permission inheritance through folder hierarchy
- User group management

### 3.2 Folder Management
- Create, read, update, delete (CRUD) operations for folders
- Hierarchical folder structure support
- Folder-level permission assignment
- Bulk permission management

### 3.3 Document Management
- Document upload with metadata
- Support for multiple file formats (PDF, DOCX, TXT, MD, HTML)
- Document versioning
- Document deletion with vector cleanup

### 3.4 Access Control
- Folder-level permissions (read, write, delete, admin)
- Permission inheritance from parent folders
- Override permissions at sub-folder level
- Audit logging for all access attempts

### 3.5 RAG Operations
- Query processing with user context
- Vector similarity search within permitted folders
- Result filtering based on access permissions
- Context window management

## 4. Technical Architecture

### 4.1 System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │     │   Mobile App    │     │     API Client  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                         │
         └───────────────────────┴─────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      API Gateway        │
                    │    (Kong/Traefik)       │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐    ┌──────────▼────────┐    ┌─────────▼────────┐
│  Auth Service  │    │  Document Service │    │   RAG Service    │
│   (FastAPI)    │    │    (FastAPI)      │    │   (FastAPI)      │
└───────┬────────┘    └──────────┬────────┘    └─────────┬────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    PostgreSQL + pgvector│
                    │  ┌──────────────────┐  │
                    │  │ Tables:          │  │
                    │  │ - users          │  │
                    │  │ - folders        │  │
                    │  │ - documents      │  │
                    │  │ - permissions    │  │
                    │  │ - embeddings     │  │
                    │  └──────────────────┘  │
                    └─────────────────────────┘
```

### 4.2 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Folders table
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, parent_id)
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folder_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    file_hash VARCHAR(64),
    metadata JSONB,
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permissions table
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    permission_type VARCHAR(20) NOT NULL, -- 'read', 'write', 'delete', 'admin'
    granted_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, folder_id, permission_type)
);

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536), -- Assuming OpenAI embeddings
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- Create indexes for performance
CREATE INDEX idx_embeddings_document_id ON embeddings(document_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_permissions_user_folder ON permissions(user_id, folder_id);
CREATE INDEX idx_documents_folder ON documents(folder_id);
```

### 4.3 Technology Stack

#### Backend Services
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Vector Operations**: pgvector
- **Authentication**: Firebase based integration
- **Task Queue**: Celery with Redis
- **Embeddings**: OpenAI API / Sentence Transformers

#### Database
- **Primary Database**: PostgreSQL 15+ with pgvector extension
- **Cache**: Redis 7+
- **Object Storage**: MinIO (S3-compatible)

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes (Not required in the current scope)
- **Reverse Proxy**: Nginx/Traefik
- **Monitoring**: Prometheus + Grafana (Not required in the current scope)
- **Logging**: ELK Stack (Not required in the current scope)

## 5. API Specifications

### 5.1 Authentication Endpoints

```yaml
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

### 5.2 Folder Management Endpoints

```yaml
GET    /api/v1/folders              # List accessible folders
POST   /api/v1/folders              # Create new folder
GET    /api/v1/folders/{id}         # Get folder details
PUT    /api/v1/folders/{id}         # Update folder
DELETE /api/v1/folders/{id}         # Delete folder
GET    /api/v1/folders/{id}/permissions  # Get folder permissions
POST   /api/v1/folders/{id}/permissions  # Grant permissions
DELETE /api/v1/folders/{id}/permissions/{permission_id}  # Revoke permission
```

### 5.3 Document Management Endpoints

```yaml
POST   /api/v1/folders/{folder_id}/documents     # Upload document
GET    /api/v1/documents/{id}                    # Download document
DELETE /api/v1/documents/{id}                    # Delete document
GET    /api/v1/documents/{id}/metadata           # Get document metadata
```

### 5.4 RAG Endpoints

```yaml
POST   /api/v1/rag/query                         # Submit RAG query
GET    /api/v1/rag/query/{query_id}/status       # Check query status
GET    /api/v1/rag/query/{query_id}/results      # Get query results
```

## 6. Security Requirements

### 6.1 Authentication & Authorization
- JWT-based authentication with short-lived access tokens
- Refresh token rotation
- Multi-factor authentication support (Not required in the current scope)
- Session management with Redis (Not required in the current scope)

### 6.2 Data Security
- Encryption at rest for sensitive data
- TLS 1.3 for all communications
- Document encryption before storage
- Secure key management using environment variables

### 6.3 Access Control
- Row-level security in PostgreSQL
- Query-time permission checks
- Audit logging for all data access
- Rate limiting per user/API key

### 6.4 Container Security
- Non-root container execution
- Read-only root filesystem
- Security scanning of base images
- Secrets management via environment variables

## 7. Containerization Strategy

### 7.1 Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: ragdb
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rag_network

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - rag_network

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    networks:
      - rag_network

  auth_service:
    build:
      context: ./services/auth
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ragdb
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - postgres
      - redis
    networks:
      - rag_network

  document_service:
    build:
      context: ./services/document
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ragdb
      MINIO_ENDPOINT: http://minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
    depends_on:
      - postgres
      - minio
    networks:
      - rag_network

  rag_service:
    build:
      context: ./services/rag
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ragdb
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - rag_network

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - auth_service
      - document_service
      - rag_service
    networks:
      - rag_network

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  rag_network:
    driver: bridge
```

### 7.2 Dockerfile Template

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 8. Conclusion

This RAG solution with RBAC provides a secure, scalable platform for document management and retrieval. The containerized architecture ensures cloud portability while maintaining strict access controls and data isolation between users and folders.