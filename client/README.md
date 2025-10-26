# RADEX Client

A modern React/Next.js client for the RADEX RAG (Retrieval-Augmented Generation) system with Role-Based Access Control.

## Features

- 🔐 **Firebase Authentication** - Email/password and OAuth (Google, Microsoft, Okta) authentication via Firebase
- 📁 **Folder Management** - Hierarchical folder structure with granular permissions
- 📄 **Document Management** - Upload, organize, and manage documents with drag-and-drop
- 🤖 **RAG Chat Interface** - AI-powered document questioning with source citations
- 📱 **Responsive Design** - Mobile-first design that works on all devices
- ⚡ **Real-time Updates** - Live document processing status and chat responses
- 🎨 **Modern UI** - Clean, professional split-screen interface with gradient backgrounds

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Authentication**: Firebase Authentication
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
- Firebase project (for authentication)

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

## Authentication

RADEX uses Firebase Authentication for all authentication methods, providing a secure and scalable authentication solution.

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
   - Set `NEXT_PUBLIC_ENABLE_MICROSOFT_LOGIN=true` to enable
   - Requires Microsoft provider configured in Firebase Console

4. **Okta OIDC** (Optional - controlled by env flag)
   - Sign in with Okta accounts
   - Set `NEXT_PUBLIC_ENABLE_OKTA_LOGIN=true` to enable
   - Requires Okta OIDC provider configured in Firebase Console

### Firebase Setup

1. **Create a Firebase Project**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project or use an existing one

2. **Enable Authentication Providers**
   - Navigate to Authentication > Sign-in method
   - Enable Email/Password provider
   - Enable Google provider
   - (Optional) Enable Microsoft provider
   - (Optional) Configure Okta OIDC provider

3. **Get Firebase Configuration**
   - Go to Project Settings > General
   - Scroll to "Your apps" section
   - Click "Web app" and copy the configuration
   - Add the values to your `.env.local` file

4. **Configure Firebase Admin SDK (Server-side)**
   - See server README for Firebase Admin SDK setup
   - Required for verifying Firebase ID tokens on the backend

### Authentication Flow

1. User signs up/logs in using any authentication method
2. Firebase authenticates the user and returns an ID token
3. Client sends the Firebase ID token to the RADEX server
4. Server verifies the token using Firebase Admin SDK
5. Server creates/updates user record with appropriate provider information
6. User is authenticated and can access protected resources

### Landing Page

The login and registration pages feature a modern split-screen design:

- **Left Side** (hidden on mobile):
  - Gradient background with app branding
  - Feature highlights with icons
  - Built with tech stack information

- **Right Side**:
  - Clean authentication form
  - Email/password login
  - OAuth provider buttons (conditionally displayed)
  - Sign up/sign in navigation

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

### Project Structure

```
client/
├── src/
│   ├── app/              # Next.js app router pages
│   ├── components/       # React components
│   │   ├── auth/        # Authentication components (LoginForm, RegisterForm)
│   │   └── ui/          # Reusable UI components
│   ├── contexts/         # React contexts (AuthContext)
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities
│   │   ├── api.ts       # API client
│   │   └── firebase.ts  # Firebase configuration and helpers
│   └── types/            # TypeScript type definitions
├── public/               # Static assets
└── .env.local           # Environment variables (not in git)
```

## Security Considerations

- All authentication goes through Firebase
- No passwords are stored on the RADEX server
- Firebase ID tokens are verified on the server using Firebase Admin SDK
- Tokens are automatically refreshed by Firebase
- Environment flags allow fine-grained control over authentication methods

## Troubleshooting

### Firebase Authentication Issues

**Problem**: "Firebase not initialized" error
- **Solution**: Ensure all Firebase environment variables are set correctly in `.env.local`

**Problem**: OAuth provider not showing
- **Solution**: Check that the provider is enabled both in Firebase Console and via environment flag (for Microsoft/Okta)

**Problem**: "Invalid authentication token" error
- **Solution**: Ensure Firebase Admin SDK is properly configured on the server with the correct service account credentials

### Build Issues

**Problem**: Build fails with environment variable errors
- **Solution**: Make sure all required `NEXT_PUBLIC_*` variables are set in `.env.local`

**Problem**: Type errors in authentication code
- **Solution**: Run `npm install` to ensure all dependencies are up to date

## License

This project is licensed under the MIT License.
