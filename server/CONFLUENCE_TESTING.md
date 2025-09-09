# Confluence API Testing Guide

This guide shows how to test the Confluence integration APIs manually using curl commands.

## Prerequisites

1. **Server Running**: Make sure the FastAPI server is running on port 8000
```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Authentication**: Get a JWT token by logging in
```bash
# Register a user (if needed)
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Login and get token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')

echo "Your token: $TOKEN"
```

## API Endpoints Testing

### 1. Authentication Management

#### Create Confluence Credentials
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/auth" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confluence_type": "cloud",
    "base_url": "https://yourcompany.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "your-confluence-api-token"
  }' | jq .
```

#### List All Credentials
```bash
curl -X GET "http://localhost:8000/api/v1/confluence/auth" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

#### Check Credential Status
```bash
CREDENTIAL_ID="your-credential-id-here"
curl -X GET "http://localhost:8000/api/v1/confluence/auth/status/$CREDENTIAL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

#### Delete Credentials
```bash
curl -X DELETE "http://localhost:8000/api/v1/confluence/auth/$CREDENTIAL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 2. Content Discovery

#### Get Confluence Spaces
```bash
curl -X GET "http://localhost:8000/api/v1/confluence/spaces?credential_id=$CREDENTIAL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

#### Get Pages in a Space
```bash
SPACE_KEY="TEST"
curl -X GET "http://localhost:8000/api/v1/confluence/spaces/$SPACE_KEY/pages?credential_id=$CREDENTIAL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

#### Search Confluence Content
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "'$CREDENTIAL_ID'",
    "query": "documentation",
    "search_type": "text",
    "limit": 10
  }' | jq .
```

### 3. Content Import

#### Create a Folder First (Required)
```bash
# Create a folder to import content into
FOLDER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/folders/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Confluence Imports",
    "parent_id": null
  }')

FOLDER_ID=$(echo $FOLDER_RESPONSE | jq -r '.id')
echo "Created folder with ID: $FOLDER_ID"
```

#### Import a Single Page
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/import" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "'$CREDENTIAL_ID'",
    "folder_id": "'$FOLDER_ID'",
    "import_type": "page",
    "page_id": "123456789",
    "include_attachments": true,
    "include_comments": false,
    "recursive": false
  }' | jq .
```

#### Import Entire Space
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/import" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "'$CREDENTIAL_ID'",
    "folder_id": "'$FOLDER_ID'",
    "import_type": "space",
    "space_key": "TEST",
    "include_attachments": true,
    "include_comments": false,
    "recursive": true
  }' | jq .
```

#### Import Page Tree
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/import" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "'$CREDENTIAL_ID'",
    "folder_id": "'$FOLDER_ID'",
    "import_type": "page_tree",
    "page_id": "123456789",
    "include_attachments": true,
    "include_comments": false,
    "recursive": true
  }' | jq .
```

#### Batch Import
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/import/batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "'$CREDENTIAL_ID'",
    "folder_id": "'$FOLDER_ID'",
    "imports": [
      {
        "import_type": "page",
        "page_id": "123456789"
      },
      {
        "import_type": "page",
        "page_id": "987654321"
      }
    ]
  }' | jq .
```

### 4. Import Status Tracking

#### Check Import Status
```bash
IMPORT_ID="your-import-job-id"
curl -X GET "http://localhost:8000/api/v1/confluence/import/$IMPORT_ID/status" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 5. Content Synchronization

#### Manual Sync
```bash
curl -X POST "http://localhost:8000/api/v1/confluence/sync/$IMPORT_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

#### Get Sync History
```bash
curl -X GET "http://localhost:8000/api/v1/confluence/sync/history?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## Example Workflow

Here's a complete example workflow:

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')

# 2. Add Confluence credentials
CRED_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/confluence/auth" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confluence_type": "cloud",
    "base_url": "https://yourcompany.atlassian.net",
    "email": "your-email@company.com",
    "api_token": "your-api-token"
  }')

CREDENTIAL_ID=$(echo $CRED_RESPONSE | jq -r '.id')

# 3. Create a folder for imports
FOLDER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/folders/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Confluence Import", "parent_id": null}')

FOLDER_ID=$(echo $FOLDER_RESPONSE | jq -r '.id')

# 4. List available spaces
curl -X GET "http://localhost:8000/api/v1/confluence/spaces?credential_id=$CREDENTIAL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. Import a space
IMPORT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/confluence/import" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "credential_id": "'$CREDENTIAL_ID'",
    "folder_id": "'$FOLDER_ID'",
    "import_type": "space",
    "space_key": "TEST",
    "include_attachments": true
  }')

IMPORT_ID=$(echo $IMPORT_RESPONSE | jq -r '.id')

# 6. Monitor import progress
curl -X GET "http://localhost:8000/api/v1/confluence/import/$IMPORT_ID/status" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## Testing with Real Confluence Instance

To test with a real Confluence instance:

1. **For Confluence Cloud:**
   - Get an API token from: https://id.atlassian.com/manage-profile/security/api-tokens
   - Use `confluence_type: "cloud"`
   - Use your Atlassian email and the API token

2. **For Confluence Server/Data Center:**
   - Get an API token from your Confluence admin
   - Use `confluence_type: "server"`
   - Use your Confluence email and the API token

3. **Replace placeholder values:**
   - `https://yourcompany.atlassian.net` with your actual Confluence URL
   - `your-email@company.com` with your actual email
   - `your-api-token` with your actual API token
   - Space keys and page IDs with real ones from your Confluence

## Error Handling

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid token)
- `403`: Forbidden (no permission)
- `404`: Not Found (resource doesn't exist)
- `422`: Validation Error (invalid data format)

All error responses include a `detail` field with the error message.

## Background Processing

Import operations run in the background. Use the status endpoint to monitor progress:

```bash
# Keep checking until status is "completed", "failed", or "partial"
while true; do
  STATUS=$(curl -s -X GET "http://localhost:8000/api/v1/confluence/import/$IMPORT_ID/status" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "completed" ]] || [[ "$STATUS" == "failed" ]] || [[ "$STATUS" == "partial" ]]; then
    break
  fi
  sleep 5
done
```