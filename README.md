# RAG Solution with Role-Based Access Control

![Health Check](https://github.com/sapieonic/radex/workflows/Health%20Check/badge.svg)
![Smoke Tests](https://github.com/sapieonic/radex/workflows/Smoke%20Tests/badge.svg)

A comprehensive Retrieval-Augmented Generation (RAG) solution with role-based access control, built with FastAPI, PostgreSQL, and OpenAI.

## ✨ Features

- 🔐 **JWT Authentication** - Secure user authentication with token management
- 📁 **Hierarchical Folders** - Organize documents with nested folder structure
- 📄 **Document Management** - Upload, process, and manage various file types
- 🤖 **AI-Powered RAG** - Query documents with natural language using OpenAI
- 🛡️ **Role-Based Access Control** - Granular permissions at folder and document levels
- 🔍 **Vector Search** - Semantic document search with pgvector
- 📊 **Health Monitoring** - Built-in health checks and monitoring
- 🐳 **Docker Support** - Complete containerized deployment

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - For running services
- **Python 3.11+** - For local development
- **Git** - For version control
- **OpenAI API Key** - Optional, for RAG functionality

### 1. Clone the Repository

```bash
git clone https://github.com/sapieonic/radex.git
cd radex
```

### 2. Environment Configuration

```bash
cd server
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Required - Change these values
JWT_SECRET_KEY=your-secret-key-here-change-this
OPENAI_API_KEY=your-openai-api-key-here

# Database (defaults work for Docker setup)
DATABASE_URL=postgresql+psycopg://raguser:changeme@localhost:5432/ragdb

# Optional - Customize as needed
APP_NAME=RAG RBAC System
DEBUG=false
```

### 3. Choose Your Setup Method

#### Option A: Full Docker Setup (Recommended)

```bash
# Start all services including the API server
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

#### Option B: Development Setup

```bash
# Start infrastructure services only
docker-compose up -d postgres redis minio

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the Application

Once running, you can access:

- **🔗 API Documentation**: http://localhost:8000/docs
- **🔗 Health Check**: http://localhost:8000/health  
- **🔗 MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## 📖 Usage Guide

### Basic Workflow

1. **Register/Login**: Create an account or authenticate
2. **Create Folders**: Organize your documents in folders
3. **Upload Documents**: Add PDF, Word, text, or markdown files
4. **Set Permissions**: Control access for other users
5. **Query with RAG**: Ask questions about your documents

### API Examples

#### Authentication
```bash
# Register new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "testuser", "password": "securepass123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=securepass123"
```

#### Document Management
```bash
# Create folder (requires auth token)
curl -X POST "http://localhost:8000/api/v1/folders" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Documents"}'

# Upload document
curl -X POST "http://localhost:8000/api/v1/folders/{folder_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

#### RAG Queries
```bash
# Query documents
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main topics?", "folder_ids": ["folder-id"]}'
```

## 🧪 Testing

### Running Tests

```bash
cd server

# Start test infrastructure
docker-compose -f dev-docker-compose.yml up -d

# Create virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Run smoke tests
export OPENAI_API_KEY="test-key"  # Use test key for testing
pytest tests/smoke/ -v
```

### Test Coverage

- ✅ **Authentication** - User registration, login, permissions
- ✅ **Folders** - CRUD operations, permissions, hierarchy
- ✅ **Documents** - Upload, download, metadata, access control
- ✅ **RAG** - Query processing, permission enforcement
- ✅ **End-to-End** - Complete workflow validation

## 🔧 Configuration

### Supported File Types
- **PDF** - `.pdf`
- **Word Documents** - `.docx`, `.doc`
- **Text Files** - `.txt`
- **Markdown** - `.md`
- **HTML** - `.html`, `.htm`

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | See .env.example | Yes |
| `REDIS_URL` | Redis connection string | See .env.example | Yes |
| `JWT_SECRET_KEY` | JWT signing secret | - | **Yes** |
| `OPENAI_API_KEY` | OpenAI API key for RAG | - | Optional |
| `MINIO_ENDPOINT` | MinIO endpoint | localhost:9000 | Yes |
| `MINIO_ACCESS_KEY` | MinIO access key | minioadmin | Yes |
| `MINIO_SECRET_KEY` | MinIO secret key | minioadmin | Yes |
| `DEBUG` | Enable debug mode | false | No |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend/API  │    │   FastAPI App   │    │   PostgreSQL    │
│     Client      │───▶│   + pgvector    │───▶│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                        │
                               ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     MinIO       │    │     Redis       │
                       │   (S3 Storage)  │    │   (Caching)     │
                       └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │     OpenAI      │
                       │  (Embeddings)   │
                       └─────────────────┘
```

### Core Components

- **FastAPI** - High-performance async web framework
- **PostgreSQL + pgvector** - Vector database for embeddings
- **Redis** - Caching and session management
- **MinIO** - S3-compatible object storage
- **OpenAI** - Text embeddings and completions

## 🚀 Deployment

### Docker Production Deployment

```bash
# Build and start all services
docker-compose up -d --build

# Check service health
docker-compose ps
curl http://localhost:8000/health
```

### Manual Production Setup

1. **Database Setup**
   ```bash
   # Install PostgreSQL with pgvector extension
   sudo apt install postgresql postgresql-contrib
   # Install pgvector extension (see pgvector docs)
   ```

2. **Application Deployment**
   ```bash
   # Clone and setup
   git clone https://github.com/sapieonic/radex.git
   cd radex/server
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with production values
   
   # Run with Gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🛡️ Security

- **Authentication** - JWT tokens with configurable expiration
- **Authorization** - Role-based access control (RBAC)
- **Data Validation** - Pydantic schema validation
- **File Security** - File type and size restrictions
- **Password Security** - bcrypt hashing
- **API Security** - Rate limiting and input sanitization

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes and add tests**
4. **Run the test suite**
   ```bash
   pytest tests/smoke/ -v
   ```
5. **Commit your changes**
   ```bash
   git commit -m 'feat: add amazing feature'
   ```
6. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- Follow existing code patterns and conventions
- Add tests for new functionality
- Update documentation for API changes
- Ensure all CI/CD checks pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [server README](server/README.md) for detailed documentation
- **Issues**: Open an issue on GitHub for bugs or feature requests
- **API Reference**: Visit `/docs` endpoint when running the server

---

**Built with ❤️ using FastAPI, PostgreSQL, and OpenAI**