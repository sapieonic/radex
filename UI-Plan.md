# RADEX - UI Plan

A comprehensive user interface for the RAG Solution with Role-Based Access Control (RBAC). This plan outlines the design and implementation strategy for a modern, intuitive web application with a blue and white color theme.

## Design System & Theme

### Color Palette
- **Primary Blue**: #0066CC (Navigation, buttons, primary actions)
- **Secondary Blue**: #4D94FF (Accents, hover states)
- **Light Blue**: #E6F3FF (Backgrounds, cards)
- **White**: #FFFFFF (Main backgrounds, text areas)
- **Dark Gray**: #333333 (Text, icons)
- **Light Gray**: #F5F5F5 (Borders, dividers)
- **Success**: #28A745 (Success messages, upload status)
- **Error**: #DC3545 (Error messages, validation)
- **Warning**: #FFC107 (Warnings, pending states)

### Typography
- **Primary Font**: Inter or similar modern sans-serif
- **Monospace**: JetBrains Mono for code/file names
- **Headings**: Bold, primary blue color
- **Body Text**: Dark gray, readable contrast

### Logo & Branding
- **App Name**: RADEX (displayed prominently)
- **Tagline**: "Intelligent Document Management with RBAC"

## Application Structure

### 1. Authentication Module

#### Login Page (`/login`)
- Clean, centered login form with RADEX branding
- Email/Username and password fields
- "Remember me" checkbox
- "Login" button (primary blue)
- Link to registration page
- Password reset functionality
- Error handling with clear messages

**Backend API Integration:**
- `POST /api/v1/auth/login` - User login with form data (username/password)
- Returns JWT token and user information
- Handle 401 errors for invalid credentials

#### Registration Page (`/register`)
- User registration form with validation
- Fields: Email, Username, Password, Confirm Password
- Real-time validation feedback
- Terms of service acceptance
- "Create Account" button
- Link back to login page

**Backend API Integration:**
- `POST /api/v1/auth/register` - User registration
- Payload: `{ "email": "user@example.com", "username": "testuser", "password": "securepassword123" }`
- Handle validation errors and duplicate user scenarios

#### Password Reset Flow
- Forgot password page
- Reset confirmation page
- New password setup page

**Backend API Integration:**
- `POST /api/v1/auth/refresh` - Token refresh functionality
- `GET /api/v1/auth/me` - Get current user information (for session validation)

### 2. Main Application Layout

#### Header/Navigation
- **Top Navigation Bar** (primary blue background)
  - RADEX logo/name (left)
  - Main navigation menu (center): Documents, Folders, RAG Chat
  - User dropdown (right): Profile, Settings, Logout
  - Search bar for global document search

**Backend API Integration:**
- `GET /api/v1/auth/me` - Get current user info for profile dropdown
- Logout: Clear JWT token from client storage

#### Sidebar Navigation
- **Folder Tree View** (collapsible)
  - Hierarchical folder structure
  - Expand/collapse folders
  - Folder icons with permission indicators
  - Right-click context menu for folder operations
  - "Create Folder" button at top

**Backend API Integration:**
- `GET /api/v1/folders` - List accessible folders with hierarchical structure
- Returns folders with permission levels and document counts

### 3. Dashboard/Home Page (`/`)

#### Overview Cards
- **Welcome Section** with user name
- **Quick Stats Cards**:
  - Total Documents
  - Accessible Folders
  - Recent Queries
  - Storage Used
- **Recent Activity** feed
- **Quick Actions** panel:
  - Upload Document
  - Create Folder
  - Start RAG Query

**Backend API Integration:**
- `GET /api/v1/auth/me` - User information for welcome section
- `GET /api/v1/folders` - Count accessible folders
- `GET /api/v1/rag/folders` - Count queryable folders
- `GET /api/v1/folders/{id}/documents` - Count documents across folders for statistics
- Consider adding dashboard-specific endpoints for aggregated stats

### 4. Folder Management (`/folders`)

#### Folder List View
- **Grid/List Toggle** for viewing folders
- **Folder Cards** showing:
  - Folder name and icon
  - Document count
  - Last modified date
  - Permission level indicator
  - Quick action buttons (view, edit, delete)

**Backend API Integration:**
- `GET /api/v1/folders` - List all accessible folders with metadata

#### Folder Detail Page (`/folders/:id`)
- **Folder Header**:
  - Breadcrumb navigation
  - Folder name (editable inline)
  - Permission management button
  - Folder actions dropdown

- **Documents Section**:
  - Document list/grid view
  - Upload area (drag & drop)
  - File filtering and sorting
  - Bulk actions (delete, move)

- **Subfolders Section**:
  - Nested folder display
  - Create subfolder button

**Backend API Integration:**
- `GET /api/v1/folders/{id}` - Get folder details and contents
- `GET /api/v1/folders/{id}/documents` - List documents in folder
- `POST /api/v1/folders/{folder_id}/documents` - Upload documents to folder
- `PUT /api/v1/folders/{id}` - Update folder name/details
- `DELETE /api/v1/folders/{id}` - Delete folder
- `POST /api/v1/folders` - Create new folder/subfolder

#### Permission Management Modal
- **User Search** with autocomplete
- **Permission Matrix**:
  - User/Role columns
  - Permission types (Read, Write, Delete, Admin)
  - Grant/Revoke toggles
- **Inheritance Settings**
- Save/Cancel buttons

**Backend API Integration:**
- `GET /api/v1/folders/{id}/permissions` - List current folder permissions
- `POST /api/v1/folders/{id}/permissions` - Grant permissions to users/roles
- `DELETE /api/v1/folders/{id}/permissions` - Revoke permissions
- User search endpoint (may need to be added for autocomplete)

### 5. Document Management

#### File Upload Interface
- **Drag & Drop Zone** (prominent, blue border when active)
- **File Browser** with multi-select
- **Upload Progress** indicators
- **Supported Formats** list display (.pdf, .docx, .doc, .txt, .md, .html, .htm)
- **File Size Validation** with clear limits

**Backend API Integration:**
- `POST /api/v1/folders/{folder_id}/documents` - Upload documents with multipart form data
- Handle file validation errors and processing status updates

#### Document List/Grid View
- **Document Cards** showing:
  - File type icon
  - Document name
  - File size
  - Upload date
  - Processing status
  - Quick actions (view, download, delete)

**Backend API Integration:**
- `GET /api/v1/folders/{folder_id}/documents` - List documents in specific folder
- Returns document metadata, processing status, and user permissions

#### Document Detail Modal
- **File Preview** (for supported formats)
- **Metadata Display**:
  - File information
  - Processing status
  - Permissions
  - Version history
- **Actions**: Download, Delete, Share

**Backend API Integration:**
- `GET /api/v1/documents/{id}` - Get document metadata and processing status
- `GET /api/v1/documents/{id}/download` - Download document file
- `DELETE /api/v1/documents/{id}` - Delete document

### 6. RAG Chat Interface (`/chat`)

#### Chat Layout
- **Split-screen design**:
  - Left: Folder selector and query history
  - Right: Chat interface

#### Folder Selection Panel
- **Folder Tree** with checkboxes
- **Select All/None** buttons
- **Selected Folders** summary
- Permission indicators for queryable folders

**Backend API Integration:**
- `GET /api/v1/rag/folders` - List folders available for RAG queries
- Filter based on user permissions for query access

#### Chat Interface
- **Message Thread**:
  - User queries (right-aligned, blue background)
  - AI responses (left-aligned, white background)
  - Source citations with clickable links
  - Copy message buttons
- **Input Area**:
  - Multi-line text input
  - Send button
  - Suggested queries dropdown
  - Attachment indicator for selected folders

**Backend API Integration:**
- `POST /api/v1/rag/query` - Submit RAG query
- Payload: `{ "query": "What is...", "folder_ids": ["uuid1", "uuid2"], "limit": 5 }`
- Returns AI response with source citations and document references
- `GET /api/v1/rag/health` - Check RAG system availability

#### Query Suggestions
- **Smart Suggestions** based on document content
- **Recent Queries** quick access
- **Popular Queries** from other users (if permitted)

**Backend API Integration:**
- `POST /api/v1/rag/suggest-queries` - Get query suggestions based on selected folders
- Consider storing query history in user session/database for recent queries

### 7. Admin Panel (`/admin`) - For Admin Users

#### User Management
- **User List** with search and filtering
- **User Roles** management
- **Permission Templates**
- **System Statistics**

**Backend API Integration:**
- `GET /api/v1/auth/me` - Verify admin permissions before showing panel
- User management endpoints (may need to be added):
  - `GET /api/v1/admin/users` - List all users with roles and stats
  - `PUT /api/v1/admin/users/{id}` - Update user roles/status
  - `DELETE /api/v1/admin/users/{id}` - Deactivate/delete users
- System statistics endpoints (may need to be added):
  - `GET /api/v1/admin/stats` - Overall system usage statistics

#### System Settings
- **Configuration Panel**
- **Integration Settings** (OpenAI, MinIO)
- **Security Settings**
- **Backup & Maintenance**

**Backend API Integration:**
- System configuration endpoints (may need to be added):
  - `GET /api/v1/admin/config` - Get system configuration
  - `PUT /api/v1/admin/config` - Update system settings
- `GET /api/v1/rag/health` - System health monitoring

### 8. User Profile & Settings (`/profile`)

#### Profile Management
- **Personal Information** editing
- **Password Change** functionality
- **Account Settings**
- **Notification Preferences**

**Backend API Integration:**
- `GET /api/v1/auth/me` - Get current user profile information
- User profile endpoints (may need to be added):
  - `PUT /api/v1/auth/profile` - Update user profile information
  - `POST /api/v1/auth/change-password` - Change user password
  - `PUT /api/v1/auth/preferences` - Update user preferences

#### Application Preferences
- **Theme Settings** (if multiple themes supported)
- **Default Folder Views**
- **Language Settings**
- **Export/Import** personal data

**Backend API Integration:**
- User preferences stored client-side or via profile endpoints
- Data export functionality (may need to be added):
  - `GET /api/v1/auth/export-data` - Export user data and documents

### 9. Responsive Design

#### Mobile Layout (`< 768px`)
- **Hamburger Menu** for navigation
- **Collapsible Sidebar**
- **Touch-Friendly** buttons and interactions
- **Swipe Gestures** for document browsing
- **Mobile-Optimized** chat interface

#### Tablet Layout (`768px - 1024px`)
- **Adaptive Sidebar** (collapsible)
- **Grid Adjustments** for optimal viewing
- **Touch Support** maintained

### 10. Component Library

#### Common UI Components
- **Buttons**: Primary, Secondary, Danger, Ghost
- **Form Inputs**: Text, Email, Password, File Upload
- **Modals**: Confirmation, Form, Detail view
- **Notifications**: Success, Error, Warning, Info
- **Loading States**: Spinners, Progress bars, Skeleton screens
- **Cards**: Document, Folder, User, Statistics
- **Dropdowns**: Menu, Select, User profile
- **Breadcrumbs**: Navigation trail
- **Pagination**: Document/folder lists
- **Tooltips**: Contextual help

#### Data Display
- **Tables**: Sortable, filterable data
- **Tree View**: Folder hierarchy
- **Timeline**: Activity feeds
- **Charts**: Usage statistics (if needed)

### 11. Error Handling & Loading States

#### Error Pages
- **404 Not Found** with navigation
- **403 Forbidden** with clear explanation
- **500 Server Error** with retry option
- **Network Error** with offline indicator

#### Loading States
- **Document Processing** progress
- **Chat Response** typing indicators
- **File Upload** progress bars
- **Search Results** loading skeletons

### 12. Accessibility & UX

#### Accessibility Features
- **WCAG 2.1 AA** compliance
- **Keyboard Navigation** support
- **Screen Reader** compatibility
- **High Contrast** mode support
- **Focus Indicators** clearly visible

#### User Experience
- **Confirmation Dialogs** for destructive actions
- **Undo Functionality** where appropriate
- **Auto-save** for forms
- **Keyboard Shortcuts** for power users
- **Contextual Help** and tooltips

### 13. Performance Considerations

#### Optimization Strategies
- **Lazy Loading** for document lists
- **Virtual Scrolling** for large datasets
- **Image Optimization** for document previews
- **Caching Strategy** for API responses
- **Progressive Loading** for chat history

#### Bundle Optimization
- **Code Splitting** by route
- **Tree Shaking** for unused code
- **Asset Compression** and optimization
- **CDN Integration** for static assets

### 14. Security Features

#### Client-Side Security
- **JWT Token** management
- **Secure Storage** of sensitive data
- **CSRF Protection**
- **Input Sanitization**
- **Permission-Based UI** rendering

#### Privacy Considerations
- **Data Encryption** in transit
- **Minimal Data Exposure**
- **Audit Trail** for sensitive actions
- **Session Management**

## Technology Stack Recommendations

### Frontend Framework
- **React** with TypeScript
- **Next.js** for SSR/routing
- **Tailwind CSS** for styling
- **React Query** for state management
- **React Hook Form** for form handling

### Additional Libraries
- **Framer Motion** for animations
- **React DND** for drag-and-drop
- **React Virtualized** for large lists
- **Date-fns** for date handling
- **React Icons** for consistent iconography

### Development Tools
- **ESLint** and **Prettier** for code quality
- **Storybook** for component development
- **Jest** and **React Testing Library** for testing
- **Cypress** for E2E testing

## Implementation Phases

### Phase 1: Core Authentication & Layout
- Authentication pages and flows
- Main application layout
- Basic navigation
- User profile management

### Phase 2: Folder & Document Management
- Folder CRUD operations
- Document upload and management
- Permission management interface
- File preview capabilities

### Phase 3: RAG Chat Interface
- Chat UI implementation
- Folder selection for queries
- Response formatting with citations
- Query suggestions

### Phase 4: Advanced Features
- Admin panel
- Advanced search
- Mobile responsiveness
- Performance optimizations

### Phase 5: Polish & Deployment
- Accessibility improvements
- Error handling refinement
- Testing and bug fixes
- Deployment configuration

## Backend API Reference

This section consolidates all the backend API endpoints mentioned throughout the UI plan for easy reference during implementation.

### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration
  - Payload: `{ "email": "user@example.com", "username": "testuser", "password": "securepassword123" }`
- `POST /api/v1/auth/login` - User login (form data)
  - Payload: `username=testuser&password=securepassword123`
- `GET /api/v1/auth/me` - Get current user information
- `POST /api/v1/auth/refresh` - Refresh JWT token

### Folder Management Endpoints
- `GET /api/v1/folders` - List accessible folders with hierarchical structure
- `POST /api/v1/folders` - Create new folder
  - Payload: `{ "name": "My Documents", "parent_id": null }`
- `GET /api/v1/folders/{id}` - Get folder details and contents
- `PUT /api/v1/folders/{id}` - Update folder name/details
- `DELETE /api/v1/folders/{id}` - Delete folder
- `GET /api/v1/folders/{id}/permissions` - List folder permissions
- `POST /api/v1/folders/{id}/permissions` - Grant permissions
- `DELETE /api/v1/folders/{id}/permissions` - Revoke permissions

### Document Management Endpoints
- `POST /api/v1/folders/{folder_id}/documents` - Upload documents (multipart form)
- `GET /api/v1/folders/{folder_id}/documents` - List documents in folder
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents/{id}/download` - Download document file
- `DELETE /api/v1/documents/{id}` - Delete document

### RAG System Endpoints
- `GET /api/v1/rag/folders` - List folders available for RAG queries
- `POST /api/v1/rag/query` - Submit RAG query
  - Payload: `{ "query": "What is...", "folder_ids": ["uuid1", "uuid2"], "limit": 5 }`
- `POST /api/v1/rag/suggest-queries` - Get query suggestions
- `GET /api/v1/rag/health` - RAG system health check

### Admin Endpoints (May Need Implementation)
- `GET /api/v1/admin/users` - List all users with roles and stats
- `PUT /api/v1/admin/users/{id}` - Update user roles/status
- `DELETE /api/v1/admin/users/{id}` - Deactivate/delete users
- `GET /api/v1/admin/stats` - System usage statistics
- `GET /api/v1/admin/config` - Get system configuration
- `PUT /api/v1/admin/config` - Update system settings

### User Profile Endpoints (May Need Implementation)
- `PUT /api/v1/auth/profile` - Update user profile information
- `POST /api/v1/auth/change-password` - Change user password
- `PUT /api/v1/auth/preferences` - Update user preferences
- `GET /api/v1/auth/export-data` - Export user data and documents

### Additional Endpoints to Consider
- User search endpoint for permission management autocomplete
- Dashboard statistics endpoint for aggregated data
- Query history endpoints for RAG chat interface
- System health monitoring endpoints

### Authentication & Authorization
All endpoints except `/auth/register` and `/auth/login` require JWT authentication:
- Include `Authorization: Bearer <token>` header in requests
- Handle 401 (Unauthorized) responses by redirecting to login
- Handle 403 (Forbidden) responses with appropriate error messages
- Implement token refresh logic for expired tokens

### Error Handling
Implement consistent error handling for:
- **400 Bad Request** - Validation errors, malformed requests
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Business logic validation errors
- **500 Internal Server Error** - Server errors

This UI plan provides a comprehensive foundation for building the RADEX application with a focus on usability, security, and the specified blue and white color theme.