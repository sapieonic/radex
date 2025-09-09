# Confluence Integration for RADEX RAG System

## Executive Summary

This document outlines the plan to integrate Atlassian Confluence as a content source for the RADEX RAG (Retrieval-Augmented Generation) system. The integration will allow users to import Confluence pages and spaces, convert them to processable documents, and perform RAG operations on the content.

## Architecture Overview

### High-Level Flow

```
User Input (Confluence URL/Space) 
    → Authentication & Authorization
    → Confluence API Integration
    → Content Extraction & Transformation
    → Document Storage (MinIO)
    → Vector Embedding Generation
    → RAG-ready Content
```

## Implementation Plan

### Phase 1: Core Confluence Integration

#### 1.1 Authentication Module
**Location**: `app/services/confluence/`

- **OAuth 2.0 Integration**
  - Implement OAuth flow for Confluence Cloud
  - Store encrypted tokens in database
  - Handle token refresh automatically
  
- **API Token Support**
  - Support for Confluence Server/Data Center
  - Secure storage of API tokens per user
  
- **Database Schema Updates**
  ```sql
  -- New table for Confluence credentials
  CREATE TABLE confluence_credentials (
      id UUID PRIMARY KEY,
      user_id UUID REFERENCES users(id),
      confluence_type VARCHAR(20), -- 'cloud' or 'server'
      base_url VARCHAR(255),
      email VARCHAR(255),
      api_token_encrypted TEXT,
      oauth_token_encrypted TEXT,
      oauth_refresh_token_encrypted TEXT,
      token_expires_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP
  );
  
  -- Track imported Confluence content
  CREATE TABLE confluence_imports (
      id UUID PRIMARY KEY,
      folder_id UUID REFERENCES folders(id),
      space_key VARCHAR(50),
      page_id VARCHAR(50),
      import_type VARCHAR(20), -- 'page', 'space', 'tree'
      last_sync_at TIMESTAMP,
      sync_status VARCHAR(20),
      metadata JSONB
  );
  ```

#### 1.2 Confluence API Client
**Location**: `app/services/confluence/client.py`

- **Core Functions**:
  - `get_space_content()` - Fetch all pages in a space
  - `get_page_by_id()` - Fetch specific page
  - `get_page_tree()` - Fetch page with children
  - `get_attachments()` - Fetch page attachments
  - `get_page_history()` - Track content versions
  
- **Rate Limiting**:
  - Implement exponential backoff
  - Respect Confluence API rate limits
  - Queue system for bulk imports

### Phase 2: Content Processing Pipeline

#### 2.1 Content Extractor
**Location**: `app/services/confluence/extractor.py`

- **HTML to Markdown Conversion**:
  - Convert Confluence Storage Format to clean Markdown
  - Preserve formatting (tables, lists, code blocks)
  - Handle Confluence macros appropriately
  - Extract and process embedded images
  
- **Metadata Extraction**:
  - Page title, author, creation/modification dates
  - Labels and categories
  - Space information
  - Parent/child relationships
  
- **Attachment Processing**:
  - Download and store attachments
  - Support for images, PDFs, Office documents
  - Maintain attachment-page relationships

#### 2.2 Content Organization
**Location**: `app/services/confluence/organizer.py`

- **Folder Structure Mapping**:
  ```
  Confluence Space/
  ├── Space Home/
  │   ├── Page 1/
  │   │   ├── page_content.md
  │   │   └── attachments/
  │   └── Page 2/
  └── Child Pages/
  ```
  
- **Permission Mapping**:
  - Map Confluence permissions to RADEX RBAC
  - Handle space-level and page-level restrictions
  - Default to owner permissions for imported content

### Phase 3: API Endpoints

#### 3.1 Import Endpoints
**Location**: `app/api/v1/confluence.py`

```python
# Confluence authentication
POST /api/v1/confluence/auth
GET  /api/v1/confluence/auth/status

# Content discovery
GET  /api/v1/confluence/spaces
GET  /api/v1/confluence/spaces/{space_key}/pages
GET  /api/v1/confluence/search

# Import operations
POST /api/v1/confluence/import/page
POST /api/v1/confluence/import/space
POST /api/v1/confluence/import/batch
GET  /api/v1/confluence/import/{import_id}/status

# Sync operations
POST /api/v1/confluence/sync/{folder_id}
GET  /api/v1/confluence/sync/history
```

#### 3.2 Request/Response Schemas
**Location**: `app/schemas/confluence.py`

```python
class ConfluenceImportRequest(BaseModel):
    source_type: Literal["page", "space", "page_tree"]
    confluence_url: Optional[str]
    space_key: Optional[str]
    page_id: Optional[str]
    target_folder_id: UUID
    include_attachments: bool = True
    include_comments: bool = False
    recursive: bool = True
    
class ConfluenceImportResponse(BaseModel):
    import_id: UUID
    status: str
    total_pages: int
    processed_pages: int
    errors: List[str]
    created_documents: List[DocumentInfo]
```

### Phase 4: Background Processing

#### 4.1 Async Import Worker
**Location**: `app/workers/confluence_import.py`

- **Celery/Background Tasks**:
  - Queue large import jobs
  - Progress tracking and reporting
  - Error handling and retry logic
  - Webhook notifications on completion
  
- **Import Workflow**:
  1. Validate Confluence credentials
  2. Fetch content list
  3. Create folder structure in RADEX
  4. Process each page/attachment
  5. Generate embeddings
  6. Update import status
  7. Send completion notification

#### 4.2 Sync Mechanism
**Location**: `app/workers/confluence_sync.py`

- **Incremental Updates**:
  - Track last sync timestamp
  - Fetch only modified content
  - Update existing documents
  - Handle deleted content
  
- **Scheduled Sync**:
  - Configurable sync intervals
  - Manual sync triggers
  - Conflict resolution strategies

### Phase 5: UI Integration

#### 5.1 Frontend Components
**Location**: `client/src/components/confluence/`

- **Import Wizard**:
  - Confluence connection setup
  - Space/page browser
  - Import options selection
  - Progress monitoring
  
- **Sync Dashboard**:
  - View imported content
  - Sync status and history
  - Manual sync triggers
  - Error logs and debugging

### Phase 6: Security & Performance

#### 6.1 Security Measures

- **Credential Encryption**:
  - AES-256 encryption for stored tokens
  - Key rotation mechanism
  - Secure credential deletion
  
- **Access Control**:
  - Validate user permissions before import
  - Respect Confluence access restrictions
  - Audit logging for all operations

#### 6.2 Performance Optimization

- **Caching Strategy**:
  - Cache frequently accessed Confluence data
  - Redis-based response caching
  - ETags for conditional requests
  
- **Batch Processing**:
  - Chunk large imports
  - Parallel processing where possible
  - Connection pooling for API requests

## Technical Dependencies

### New Python Packages
```python
# requirements.txt additions
atlassian-python-api==3.41.0  # Confluence API client
beautifulsoup4==4.12.2        # HTML parsing
markdownify==0.11.6           # HTML to Markdown
celery==5.3.0                 # Background tasks
cryptography==41.0.0          # Token encryption
```

### Environment Variables
```env
# Confluence Configuration
CONFLUENCE_OAUTH_CLIENT_ID=
CONFLUENCE_OAUTH_CLIENT_SECRET=
CONFLUENCE_OAUTH_REDIRECT_URI=
CONFLUENCE_ENCRYPTION_KEY=
CONFLUENCE_MAX_IMPORT_SIZE=100  # MB
CONFLUENCE_RATE_LIMIT=10  # requests per second
CONFLUENCE_SYNC_INTERVAL=3600  # seconds
```

## Database Migrations

### Migration Scripts
```python
# alembic/versions/xxx_add_confluence_support.py
def upgrade():
    # Create confluence_credentials table
    # Create confluence_imports table
    # Add confluence_metadata column to documents table
    
def downgrade():
    # Reverse all changes
```

## Conclusion

This Confluence integration will significantly expand RADEX's capabilities by allowing organizations to leverage their existing Confluence knowledge base for RAG operations. The phased approach ensures a robust, scalable, and secure implementation while maintaining the system's core RBAC principles.