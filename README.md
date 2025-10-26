# RADEX - RAG Document Explorer

A comprehensive Retrieval-Augmented Generation (RAG) system with Role-Based Access Control (RBAC), featuring a modern React/Next.js frontend and FastAPI backend. RADEX enables organizations to securely manage, share, and query documents using AI-powered search and question-answering capabilities.

## 🚀 Features

### Core Capabilities
- **🤖 AI-Powered RAG**: Query documents using natural language with OpenAI-powered responses and source citations
- **🔐 Firebase Authentication**: Secure authentication with Email/Password and OAuth (Google, Microsoft, Okta)
- **👥 Role-Based Access Control**: Granular permissions at folder and document levels
- **📁 Hierarchical Organization**: Nested folder structure with permission inheritance
- **📄 Multi-Format Support**: Process PDF, Word, Text, Markdown, and HTML documents
- **☁️ S3-Compatible Storage**: MinIO object storage for scalable file management
- **📱 Responsive UI**: Modern React/Next.js interface with split-screen authentication design
- **⚡ Real-time Updates**: Live document processing status and chat responses

### Technical Features
- **Vector Embeddings**: Automatic document processing with OpenAI embeddings and pgvector
- **Source Citations**: RAG responses include document references
- **Drag-and-Drop Uploads**: Intuitive file upload interface
- **Admin Dashboard**: Comprehensive user and system management
- **Health Monitoring**: Built-in health checks for all services
- **Caching Layer**: Redis for improved performance

## 🏗️ Architecture

```
RADEX/
├── server/              # FastAPI backend
│   ├── app/            # Application code
│   ├── tests/          # Test suites
│   └── docker-compose.yml
├── client/              # Next.js frontend
│   ├── src/            # React components
│   ├── public/         # Static assets
│   └── package.json
└── docker-compose.yml   # Full-stack orchestration
```

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL with pgvector extension
- Redis for caching
- MinIO for S3-compatible object storage
- OpenAI API for embeddings & RAG

**Frontend:**
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- React Query for state management
- React Hook Form with Zod validation
- Lucide React for icons
- Axios for API communication

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for client development)
- Python 3.11+ (for server development)
- OpenAI API Key (for RAG functionality)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/radex.git
cd radex
```

### 2. Configure Environment

#### Server Configuration
```bash
cd server
cp .env.example .env
# Edit .env with your configuration
```

**Required server environment variables:**
```env
# IMPORTANT: Change these
OPENAI_API_KEY=your-openai-api-key-here
JWT_SECRET_KEY=change-this-to-a-secure-random-string

# Database (defaults work for Docker)
DATABASE_URL=postgresql://raguser:changeme@postgres:5432/ragdb

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Redis
REDIS_URL=redis://:changeme@redis:6379/0
```

#### Client Configuration
```bash
cd ../client
cp .env.local.example .env.local
# Edit .env.local with your Firebase configuration
```

**Client environment variables:**
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application Configuration
NEXT_PUBLIC_APP_NAME=RADEX
NEXT_PUBLIC_MAX_FILE_SIZE=10485760

# Authentication Configuration
# Toggle OAuth providers (both default to false)
NEXT_PUBLIC_ENABLE_MICROSOFT_LOGIN=false
NEXT_PUBLIC_ENABLE_OKTA_LOGIN=false

# Firebase Configuration
# Get these from Firebase Console -> Project Settings -> General -> Your apps -> Web app
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=your-measurement-id
```

### 3. Start the Application

#### Option A: Full Stack with Docker (Recommended)

From the root directory:
```bash
# Start all services (backend + frontend + infrastructure)
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

Services will be available at:
- **Client UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

#### Option B: Development Mode

**Terminal 1 - Backend:**
```bash
cd server

# Start infrastructure only
docker-compose up -d postgres redis minio

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Initial Setup

#### Default Admin Account

The system automatically creates a default admin user:
- **Username**: `admin`
- **Password**: `admin123456`
- **Email**: `admin@example.com`

⚠️ **Security Note**: Change the default password immediately in production!

#### Creating Additional Admin Users

```bash
cd server

# Option 1: Interactive script
./create_superuser.sh

# Option 2: Python script
python create_admin_user.py
```

## 🔐 Authentication

RADEX uses **Firebase Authentication** for all authentication methods, providing a secure and scalable authentication solution.

### Available Authentication Methods

1. **Email/Password** (Always enabled)
   - Users can sign up with email and password
   - Passwords are securely managed by Firebase
   - No passwords are stored on the RADEX server

2. **Google OAuth** (Always enabled)
   - Sign in with Google accounts
   - Requires Google provider enabled in Firebase Console

3. **Microsoft OAuth** (Optional - controlled by env flag)
   - Sign in with Microsoft accounts
   - Set `NEXT_PUBLIC_ENABLE_MICROSOFT_LOGIN=true` in client `.env.local`
   - Requires Microsoft provider configured in Firebase Console

4. **Okta OIDC** (Optional - controlled by env flag)
   - Sign in with Okta accounts
   - Set `NEXT_PUBLIC_ENABLE_OKTA_LOGIN=true` in client `.env.local`
   - Requires Okta OIDC provider configured in Firebase Console

### Firebase Setup

#### 1. Create Firebase Project
- Go to [Firebase Console](https://console.firebase.google.com/)
- Create a new project or use an existing one

#### 2. Enable Authentication Providers
- Navigate to **Authentication** > **Sign-in method**
- Enable **Email/Password** provider
- Enable **Google** provider
- (Optional) Enable **Microsoft** provider
- (Optional) Configure **Okta OIDC** provider

#### 3. Get Client Configuration
- Go to **Project Settings** > **General**
- Scroll to "Your apps" section
- Click "Web app" and copy the configuration
- Add values to `client/.env.local`

#### 4. Get Server Configuration (Firebase Admin SDK)
- Go to **Project Settings** > **Service accounts**
- Click "Generate new private key"
- Save the JSON file securely
- Set `FIREBASE_ADMIN_SDK_JSON` in `server/.env` to the JSON content (as a string)

### Authentication Flow

1. User signs up/logs in using any authentication method on the landing page
2. Firebase authenticates the user and returns an ID token
3. Client automatically sends the Firebase ID token to the RADEX server
4. Server verifies the token using Firebase Admin SDK
5. Server creates/updates user record with provider information (password/google/microsoft/okta)
6. User is authenticated and can access protected resources

### Landing Page Design

The login and registration pages feature a modern **split-screen design**:

**Left Side** (hidden on mobile):
- Gradient background (blue to indigo)
- RADEX branding
- Feature highlights with icons:
  - AI-Powered Search
  - Secure Access Control
  - Multi-Format Support
  - Team Collaboration

**Right Side**:
- Clean authentication form
- Email/password input fields
- OAuth provider buttons (Google always visible, Microsoft/Okta conditionally displayed)
- Sign up/sign in navigation

## 📚 Usage Guide

### Basic Workflow

1. **Login**: Navigate to http://localhost:3000 and sign in using:
   - Email/password (if you have an account)
   - Google (click "Google" button)
   - Microsoft (if enabled via environment flag)
   - Okta (if enabled via environment flag)
2. **Create Folders**: Organize documents in hierarchical folders
3. **Upload Documents**: Drag and drop files or use the upload button
4. **Set Permissions**: Share folders with specific users (Owner/Editor/Viewer)
5. **Query Documents**: Use the RAG chat interface to ask questions
6. **Manage Users** (Admin only): Create and manage user accounts

### Permission Levels

- **Owner**: Full control (read, write, delete, share)
- **Editor**: Can read, write, and delete
- **Viewer**: Read-only access

### Supported File Types

- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)
- Text Files (`.txt`)
- Markdown (`.md`)
- HTML (`.html`, `.htm`)

## 🧪 Testing

### Server Tests

```bash
cd server

# Start test infrastructure
docker-compose -f dev-docker-compose.yml up -d

# Set up test environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run smoke tests (integration)
pytest tests/smoke/ -v

# Run specific test suites
pytest tests/test_auth.py -v
pytest tests/smoke/test_e2e_smoke.py -v
```

### Client Tests

```bash
cd client

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Linting
npm run lint
```

## 📖 API Documentation

### Interactive Documentation

With the server running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/firebase/login` - Authenticate with Firebase ID token (primary method)
- `POST /api/v1/auth/register` - User registration (legacy - use Firebase email/password instead)
- `POST /api/v1/auth/login` - User login (legacy - use Firebase email/password instead)
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/auth/refresh` - Refresh token

#### Folders
- `GET /api/v1/folders` - List accessible folders
- `POST /api/v1/folders` - Create folder
- `PUT /api/v1/folders/{id}` - Update folder
- `DELETE /api/v1/folders/{id}` - Delete folder
- `POST /api/v1/folders/{id}/permissions` - Grant permissions

#### Documents
- `POST /api/v1/folders/{folder_id}/documents` - Upload document
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents/{id}/download` - Download document
- `DELETE /api/v1/documents/{id}` - Delete document

#### Users (Admin)
- `GET /api/v1/users/find` - Find user by email/username
- `POST /api/v1/users/` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

#### RAG
- `POST /api/v1/rag/query` - Submit RAG query
- `GET /api/v1/rag/folders` - List queryable folders
- `POST /api/v1/rag/suggest-queries` - Get query suggestions

### Example API Usage

**Note**: Authentication is handled via Firebase on the client side. The examples below show direct API usage, but in practice, the client handles Firebase authentication automatically.

```bash
# Authenticate with Firebase ID token (primary method)
# First, obtain a Firebase ID token from the client-side Firebase SDK
curl -X POST "http://localhost:8000/api/v1/auth/firebase/login" \
  -H "Content-Type: application/json" \
  -d '{"id_token": "YOUR_FIREBASE_ID_TOKEN"}'

# Legacy: Register user (use Firebase email/password signup instead)
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "testuser", "password": "secure123"}'

# Legacy: Login (use Firebase email/password login instead)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=secure123"

# Create folder (with Firebase ID token)
curl -X POST "http://localhost:8000/api/v1/folders" \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Documents"}'

# Upload document
curl -X POST "http://localhost:8000/api/v1/folders/{folder_id}/documents" \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN" \
  -F "file=@document.pdf"

# Query with RAG
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main topics?", "folder_ids": ["folder-id"]}'
```

## 🔧 Development

### Project Structure

```
radex/
├── server/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Security, dependencies
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   ├── tests/
│   │   └── smoke/         # Integration tests
│   └── requirements.txt
├── client/
│   ├── src/
│   │   ├── app/          # Next.js app router
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── lib/          # Utilities
│   │   └── types/        # TypeScript types
│   └── package.json
└── docker-compose.yml
```

### Development Scripts

**Server:**
```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
flake8 app/
```

**Client:**
```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Linting and formatting
npm run lint
npm run format
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**MinIO Connection Error**
```bash
# Check MinIO status
docker-compose logs minio

# Verify bucket creation
docker exec -it radex-minio-1 mc alias set minio http://localhost:9000 minioadmin minioadmin
docker exec -it radex-minio-1 mc mb minio/documents
```

**OpenAI API Error**
- Verify API key in server/.env
- Check API key has sufficient credits
- Ensure network connectivity to OpenAI

**Port Already in Use**
```bash
# Change ports in docker-compose.yml
# Or stop conflicting services:
lsof -i :3000  # Check what's using port 3000
lsof -i :8000  # Check what's using port 8000
```

**Client Can't Connect to Server**
- Ensure server is running on port 8000
- Check NEXT_PUBLIC_API_URL in client/.env.local
- Verify no firewall blocking connections

## 🔒 Security Considerations

### Production Deployment

1. **Firebase Authentication**:
   - Keep Firebase Admin SDK credentials secure
   - Never commit `FIREBASE_ADMIN_SDK_JSON` to version control
   - Store as environment variable or use secrets manager
   - Rotate Firebase service account keys periodically
   - Change default admin password immediately

2. **Environment Configuration**:
   - **Required**: Set up Firebase project with proper security rules
   - **Client**: Never commit `.env.local` with Firebase credentials
   - **Server**: Securely store Firebase Admin SDK JSON
   - **Database**: Use strong passwords for PostgreSQL, Redis, MinIO
   - Use secrets management in production (AWS Secrets Manager, Azure Key Vault, etc.)
   - Rotate all API keys regularly (OpenAI, Firebase, etc.)

3. **HTTPS Configuration**:
   - Set up reverse proxy (nginx/traefik)
   - Configure SSL certificates (Let's Encrypt recommended)
   - Enable HTTPS for both client and server
   - Update Firebase Auth domain to use HTTPS

4. **Database Security**:
   - Use strong passwords for all database services
   - Enable SSL/TLS connections
   - Regular backups
   - Implement database connection pooling

5. **File Upload Security**:
   - Validate file types on both client and server
   - Scan for malware
   - Set appropriate size limits (`NEXT_PUBLIC_MAX_FILE_SIZE`)
   - Use MinIO bucket policies to restrict access

6. **Authentication Best Practices**:
   - All authentication flows use Firebase (no passwords stored on server)
   - Firebase ID tokens are verified on every request
   - Tokens automatically expire and refresh
   - Environment flags control which OAuth providers are available
   - Admin users are granted via database, not Firebase

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build process or auxiliary tool changes

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/radex/issues)
- **Server Docs**: See [server/README.md](server/README.md)
- **Client Docs**: See [client/README.md](client/README.md)
- **API Reference**: http://localhost:8000/docs (when running)

## 🙏 Acknowledgments

- OpenAI for GPT and embedding models
- FastAPI for the excellent Python web framework
- Next.js team for the React framework
- PostgreSQL and pgvector teams
- All open-source contributors

---

**Built with ❤️ using FastAPI, Next.js, PostgreSQL, and OpenAI**