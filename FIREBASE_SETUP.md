# Firebase Authentication Setup Guide

This guide will walk you through setting up Firebase authentication with Google, Microsoft, and Okta providers for the RADEX application.

## Prerequisites

- A Firebase project (create one at [https://console.firebase.google.com](https://console.firebase.google.com))
- Google Cloud Platform account (for Google OAuth)
- Microsoft Azure account (for Microsoft OAuth)
- Okta account (for Okta SAML)

## Part 1: Firebase Project Setup

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add Project"
3. Enter project name (e.g., "radex-auth")
4. Follow the setup wizard

### 2. Enable Authentication Providers

#### Enable Google Sign-In

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Click on **Google**
3. Toggle **Enable**
4. Add support email
5. Click **Save**

#### Enable Microsoft Sign-In

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Click on **Microsoft**
3. Toggle **Enable**
4. You'll need to configure Azure AD (see Part 2)
5. Enter the **Application (client) ID** and **Application (client) secret** from Azure
6. Copy the **Redirect URI** provided by Firebase
7. Click **Save**

#### Enable Okta SAML

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Click on **Add new provider** → **SAML**
3. Enter provider name (e.g., "Okta")
4. Copy the **ACS URL** and **Entity ID** (you'll need these for Okta)
5. You'll need to configure Okta SAML app (see Part 3)
6. Upload the Okta IDP metadata XML or enter manually
7. Click **Save**

### 3. Get Firebase Configuration

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Scroll to "Your apps" section
3. Click the **Web** icon (</>) to add a web app
4. Register your app with a nickname (e.g., "RADEX Web")
5. Copy the Firebase configuration object

### 4. Generate Service Account Key

1. In Firebase Console, go to **Project Settings** → **Service Accounts**
2. Click **Generate New Private Key**
3. Save the JSON file securely
4. You'll use this JSON content for the `FIREBASE_ADMIN_SDK_JSON` environment variable

## Part 2: Microsoft Azure AD Setup

### 1. Register Application in Azure

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Enter name: "RADEX"
5. Select **Accounts in any organizational directory (Any Azure AD directory - Multitenant)**
6. Add Redirect URI: The one provided by Firebase (from Microsoft sign-in setup)
7. Click **Register**

### 2. Configure Application

1. Copy the **Application (client) ID**
2. Go to **Certificates & secrets**
3. Click **New client secret**
4. Add description and set expiration
5. Copy the **Value** (this is your client secret)
6. Go back to Firebase and enter these values in Microsoft provider setup

### 3. Configure API Permissions

1. Go to **API permissions**
2. Click **Add a permission** → **Microsoft Graph**
3. Select **Delegated permissions**
4. Add: `User.Read`, `email`, `openid`, `profile`
5. Click **Add permissions**
6. Click **Grant admin consent** (if you're an admin)

## Part 3: Okta SAML Setup

### 1. Create SAML Integration in Okta

1. Log in to your [Okta Admin Console](https://admin.okta.com)
2. Go to **Applications** → **Applications**
3. Click **Create App Integration**
4. Select **SAML 2.0**
5. Click **Next**

### 2. Configure SAML Settings

**General Settings:**
- App name: "RADEX"
- App logo: (optional)

**SAML Settings:**
- Single sign on URL: Use the **ACS URL** from Firebase
- Audience URI (SP Entity ID): Use the **Entity ID** from Firebase
- Name ID format: EmailAddress
- Application username: Email

**Attribute Statements:**
Add these attributes:
- `email` → `user.email`
- `firstName` → `user.firstName`
- `lastName` → `user.lastName`

### 3. Download IDP Metadata

1. After creating the app, go to the **Sign On** tab
2. Right-click on **Identity Provider metadata** link
3. Save the XML file
4. Upload this file to Firebase SAML provider configuration

### 4. Assign Users

1. Go to **Assignments** tab
2. Click **Assign** → **Assign to People/Groups**
3. Assign users who should have access

## Part 4: Backend Configuration

### 1. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your Firebase configuration:

```env
# Firebase Authentication
# Copy the entire JSON content from your service account key file
FIREBASE_ADMIN_SDK_JSON={"type":"service_account","project_id":"your-project-id",...}

# Okta Configuration (Optional - for additional Okta API features)
OKTA_CLIENT_ID=your-okta-client-id
OKTA_CLIENT_SECRET=your-okta-client-secret
OKTA_DOMAIN=your-domain.okta.com
OKTA_REDIRECT_URI=https://your-app.com/auth/callback
OKTA_API_TOKEN=your-okta-api-token
OKTA_API_AUDIENCE=your-okta-api-audience
```

**Important:** The `FIREBASE_ADMIN_SDK_JSON` must be the entire JSON object as a single-line string.

### 3. Run Database Migration

Apply the database migration to add Firebase fields:

```bash
# Using psql
psql -U raguser -d ragdb -f migrations/001_add_firebase_fields.sql

# Or using Docker
docker exec -i radex-postgres-1 psql -U raguser -d ragdb < migrations/001_add_firebase_fields.sql
```

### 4. Start the Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up
```

## Part 5: Frontend Configuration

### 1. Install Dependencies

```bash
cd client
npm install
```

### 2. Configure Environment Variables

Copy the `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your Firebase configuration:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Firebase Configuration
# Get these from Firebase Console → Project Settings → Your apps → Web app
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=your-measurement-id
```

### 3. Update Okta Provider ID (if needed)

If your Okta SAML provider ID in Firebase is different from the default, update it in `client/src/lib/firebase.ts`:

```typescript
// Line 54
const oktaProviderId = 'saml.okta';  // Replace with your actual provider ID
```

To find your provider ID:
1. Go to Firebase Console → Authentication → Sign-in method
2. Click on your SAML provider
3. The provider ID is shown at the top

### 4. Start the Frontend

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## Testing the Integration

### 1. Test Google Sign-In

1. Navigate to [http://localhost:3000/login](http://localhost:3000/login)
2. Click "Continue with Google"
3. Select your Google account
4. You should be redirected to the dashboard

### 2. Test Microsoft Sign-In

1. Navigate to [http://localhost:3000/login](http://localhost:3000/login)
2. Click "Continue with Microsoft"
3. Enter your Microsoft credentials
4. You should be redirected to the dashboard

### 3. Test Okta Sign-In

1. Navigate to [http://localhost:3000/login](http://localhost:3000/login)
2. Click "Continue with Okta"
3. You'll be redirected to Okta login page
4. Enter your Okta credentials
5. After successful authentication, you'll be redirected back to the dashboard

## Troubleshooting

### Common Issues

#### "Firebase Admin SDK initialization failed"

- Check that `FIREBASE_ADMIN_SDK_JSON` is properly formatted as a JSON string
- Ensure there are no extra newlines or spaces
- Verify the JSON is valid using a JSON validator

#### "Invalid Firebase ID token"

- Ensure the Firebase project ID matches in both frontend and backend
- Check that the token hasn't expired
- Verify the service account has the correct permissions

#### "Microsoft login fails"

- Verify the redirect URI in Azure matches exactly with Firebase
- Check that the client ID and secret are correct
- Ensure API permissions are granted

#### "Okta redirect not working"

- Verify the ACS URL and Entity ID in Okta match Firebase
- Check that the IDP metadata XML is correctly uploaded to Firebase
- Ensure users are assigned to the Okta application

### Debug Mode

Enable debug logging in the backend:

```python
# In server/app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Enable debug logging in the frontend:

```javascript
// In client/src/lib/firebase.ts
// Uncomment console.log statements
```

## Security Considerations

1. **Never commit `.env` files** to version control
2. **Rotate service account keys** regularly
3. **Use environment-specific Firebase projects** (dev, staging, prod)
4. **Enable MFA** on all admin accounts
5. **Monitor authentication logs** in Firebase Console
6. **Set up Firebase App Check** for production
7. **Implement rate limiting** on authentication endpoints
8. **Use HTTPS** in production environments

## Production Deployment

### Checklist

- [ ] Create separate Firebase projects for production
- [ ] Configure production OAuth redirect URIs
- [ ] Update environment variables for production
- [ ] Enable Firebase App Check
- [ ] Set up monitoring and alerting
- [ ] Configure CORS properly
- [ ] Use strong service account key management
- [ ] Enable audit logging
- [ ] Set up backup authentication methods
- [ ] Test all authentication flows in production

## Additional Resources

- [Firebase Authentication Documentation](https://firebase.google.com/docs/auth)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Okta SAML Documentation](https://developer.okta.com/docs/guides/build-sso-integration/)

## Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/yourusername/radex/issues)
- Review Firebase Console logs
- Check server logs for detailed error messages
