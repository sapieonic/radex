# RAG Solution with Role-Based Access Control (RBAC)

![Health Check](https://github.com/YOUR_USERNAME/radex/workflows/Health%20Check/badge.svg)
![Smoke Tests](https://github.com/YOUR_USERNAME/radex/workflows/Smoke%20Tests/badge.svg)

A comprehensive Retrieval-Augmented Generation (RAG) solution with role-based access control, built with FastAPI, PostgreSQL, and OpenAI.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- OpenAI API Key (optional for basic functionality)

### 1. Clone and Setup
```bash
git clone https://github.com/YOUR_USERNAME/radex.git
cd radex/server
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start with Docker
```bash
# Start all services
docker-compose up --build

# Or start infrastructure only (for development)
docker-compose up -d postgres redis minio
```

### 3. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Health Check**: http://localhost:8000/health

## 🏗️ Architecture

### Core Components
- **FastAPI** - High-performance API framework
- **PostgreSQL + pgvector** - Vector database for embeddings
- **Redis** - Caching and session management
- **MinIO** - S3-compatible object storage
- **OpenAI** - Text embedding and completion

### Key Features
- 🔐 **JWT Authentication** with secure password hashing
- 📁 **Hierarchical Folder Structure** with granular permissions
- 📄 **Document Management** with text extraction and processing
- 🤖 **RAG Queries** with AI-powered question answering
- 🛡️ **Role-Based Access Control** at folder and document levels
- 🐳 **Containerized Deployment** with Docker

## 🧪 Testing & CI/CD

### Automated Testing
- **Smoke Tests**: Complete system integration tests
- **Health Checks**: Daily automated health monitoring
- **GitHub Actions**: Automated testing on PR/push

### Test Coverage
- ✅ Authentication & Authorization
- ✅ Folder CRUD & Permissions
- ✅ Document Upload/Download
- ✅ RAG Functionality
- ✅ End-to-End Integration
- ✅ Resource Cleanup

### Running Tests Locally
```bash
cd server

# Start infrastructure
docker-compose -f dev-docker-compose.yml up -d

# Setup Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Run smoke tests
export OPENAI_API_KEY="test-openai-key"
pytest tests/smoke/ -v
```

## 📚 API Documentation

### Authentication Endpoints
```bash
# Register user
POST /api/v1/auth/register
# Login
POST /api/v1/auth/login
# Get current user
GET /api/v1/auth/me
# Refresh token
POST /api/v1/auth/refresh
```

### Folder Management
```bash
# Create folder
POST /api/v1/folders
# List folders
GET /api/v1/folders
# Get folder details
GET /api/v1/folders/{id}
# Update folder
PUT /api/v1/folders/{id}
# Delete folder
DELETE /api/v1/folders/{id}
# Manage permissions
POST /api/v1/folders/{id}/permissions
```

### Document Operations
```bash
# Upload document
POST /api/v1/folders/{folder_id}/documents
# Download document
GET /api/v1/documents/{id}/download
# Get document metadata
GET /api/v1/documents/{id}
# Delete document
DELETE /api/v1/documents/{id}
```

### RAG Queries
```bash
# Submit RAG query
POST /api/v1/rag/query
# Get queryable folders
GET /api/v1/rag/folders
# RAG health check
GET /api/v1/rag/health
```

## 📁 Project Structure

```
radex/
├── .github/                 # GitHub Actions workflows
│   ├── workflows/
│   │   ├── smoke-tests.yml  # Comprehensive integration tests
│   │   └── health-check.yml # Daily health monitoring
│   └── README.md           # CI/CD documentation
├── server/                 # Main application
│   ├── app/                # FastAPI application
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Security & dependencies
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   ├── tests/             # Test suites
│   │   └── smoke/         # Integration smoke tests
│   ├── docker-compose.yml # Production services
│   ├── dev-docker-compose.yml # Development services
│   └── requirements.txt   # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables
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

### Supported File Types
- **PDF**: `.pdf`
- **Word**: `.docx`, `.doc`
- **Text**: `.txt`
- **Markdown**: `.md`
- **HTML**: `.html`, `.htm`

## 🛡️ Security Features

- **JWT Authentication** with secure token management
- **Password Hashing** using bcrypt
- **Role-Based Access Control** with granular permissions
- **Input Validation** with Pydantic schemas
- **File Size Limits** and type validation
- **Permission Inheritance** in folder hierarchies

## 🚀 Deployment

### Production Deployment
```bash
# Using Docker Compose
docker-compose up -d

# Using individual containers
docker build -t rag-rbac .
docker run -d --name rag-rbac -p 8000:8000 rag-rbac
```

### Environment Setup
1. Set production environment variables
2. Configure SSL/TLS certificates
3. Set up reverse proxy (nginx/traefik)
4. Configure monitoring and logging

## 📊 Monitoring

- **Health Endpoints**: `/health` for service status
- **Metrics**: Built-in FastAPI metrics
- **Logs**: Structured logging with configurable levels
- **CI/CD**: Automated health checks and testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow
- All PRs trigger automated smoke tests
- Tests must pass before merging
- Follow existing code patterns and conventions
- Add tests for new functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [API Documentation](http://localhost:8000/docs) (when running locally)
- [GitHub Actions](.github/workflows/) (CI/CD workflows)
- [Server Documentation](server/README.md) (detailed server docs)