# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for the RAG RBAC project.

## Workflows

### Smoke Tests (`smoke-tests.yml`)

**Triggers:**
- Push to `main` branch
- Pull requests targeting `main` branch

**What it does:**
1. **Sets up infrastructure services:**
   - PostgreSQL 15 with pgvector extension
   - Redis 7 with authentication
   - MinIO for S3-compatible object storage

2. **Prepares the environment:**
   - Sets up Python 3.11
   - Installs project dependencies
   - Waits for all services to be ready
   - Initializes the database schema

3. **Runs the application:**
   - Starts FastAPI server in background
   - Verifies server health endpoint

4. **Executes smoke tests:**
   - Runs complete test suite (`tests/smoke/`)
   - Tests authentication, folders, documents, RAG, and E2E scenarios
   - Validates RBAC permissions throughout
   - Ensures proper resource cleanup

5. **Cleanup:**
   - Stops FastAPI server
   - Uploads test results as artifacts

**Test Coverage:**
- ✅ User authentication and authorization
- ✅ Folder CRUD operations with permissions
- ✅ Document upload/download with access control
- ✅ RAG functionality (without OpenAI API key)
- ✅ End-to-end system integration
- ✅ Resource cleanup validation

**Environment:**
- Uses test OpenAI API key (RAG tests adapt gracefully)
- Isolated database per workflow run
- All services run in Docker containers
- Tests run against live FastAPI application

**Duration:** ~2-3 minutes per run

## Running Tests Locally

To run the same tests locally:

```bash
# Start infrastructure services
cd server
docker-compose -f dev-docker-compose.yml up -d

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Start the server
export OPENAI_API_KEY="test-openai-key"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Run smoke tests
pytest tests/smoke/ -v
```

## Status Badge

Add this badge to your README to show CI status:

```markdown
![Smoke Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Smoke%20Tests/badge.svg)
```

## Notes

- Tests are designed to be fast and reliable
- All external dependencies are mocked or use test configurations
- Tests clean up all created resources automatically
- Workflow caches pip dependencies for faster runs