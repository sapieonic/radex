# RADEX Client

A modern React/Next.js client for the RADEX RAG (Retrieval-Augmented Generation) system with Role-Based Access Control.

## Features

- 🔐 **Authentication & Authorization** - JWT-based auth with role-based access control
- 📁 **Folder Management** - Hierarchical folder structure with granular permissions  
- 📄 **Document Management** - Upload, organize, and manage documents with drag-and-drop
- 🤖 **RAG Chat Interface** - AI-powered document questioning with source citations
- 📱 **Responsive Design** - Mobile-first design that works on all devices
- ⚡ **Real-time Updates** - Live document processing status and chat responses
- 🎨 **Modern UI** - Clean, professional interface with blue and white theme

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query + Context API
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React
- **File Uploads**: React Dropzone
- **HTTP Client**: Axios

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- RADEX Server running (see server documentation)

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment variables:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

Create a `.env.local` file with the following variables:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application Configuration  
NEXT_PUBLIC_APP_NAME=RADEX
NEXT_PUBLIC_MAX_FILE_SIZE=10485760
```

## Development

### Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint
```

## License

This project is licensed under the MIT License.