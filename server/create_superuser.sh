#!/bin/bash

# Create Superuser Script for RAG RBAC System
# This script creates a superuser by directly inserting into the database

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_USERNAME="admin"
DEFAULT_EMAIL="admin@example.com"
DEFAULT_PASSWORD="admin123456"
DOCKER_CONTAINER="server-postgres-1"
DB_USER="raguser"
DB_NAME="ragdb"

echo -e "${GREEN}RAG RBAC System - Superuser Creation Script${NC}"
echo "============================================="

# Function to generate password hash
generate_password_hash() {
    local password="$1"
    echo "Generating password hash..."
    
    # Activate virtual environment and generate hash
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        python -c "
import sys
sys.path.append('.')
from app.core.security import get_password_hash
print(get_password_hash('$password'))
" 2>/dev/null
    else
        echo -e "${RED}Error: Virtual environment not found. Please run from the server directory.${NC}"
        exit 1
    fi
}

# Function to check if Docker container is running
check_docker_container() {
    if ! docker ps --format "table {{.Names}}" | grep -q "^${DOCKER_CONTAINER}$"; then
        echo -e "${RED}Error: Docker container '${DOCKER_CONTAINER}' is not running.${NC}"
        echo "Please start your Docker containers first."
        exit 1
    fi
}

# Function to create superuser
create_superuser() {
    local username="$1"
    local email="$2"
    local password="$3"
    
    echo -e "${YELLOW}Creating superuser...${NC}"
    echo "Username: $username"
    echo "Email: $email"
    echo "Password: [hidden]"
    
    # Generate password hash
    local password_hash=$(generate_password_hash "$password")
    
    if [ -z "$password_hash" ]; then
        echo -e "${RED}Error: Failed to generate password hash${NC}"
        exit 1
    fi
    
    # Check Docker container
    check_docker_container
    
    # Create SQL command
    local sql_command="
INSERT INTO users (email, username, hashed_password, is_active, is_superuser) 
VALUES (
    '$email', 
    '$username', 
    '$password_hash',
    true, 
    true
) ON CONFLICT (email) DO UPDATE SET
    username = EXCLUDED.username,
    hashed_password = EXCLUDED.hashed_password,
    is_superuser = true,
    updated_at = CURRENT_TIMESTAMP;

-- Verify the superuser was created/updated
SELECT id, email, username, is_active, is_superuser, created_at, updated_at
FROM users 
WHERE username = '$username';"
    
    # Execute SQL command
    echo -e "${YELLOW}Executing database command...${NC}"
    docker exec -i "$DOCKER_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" <<< "$sql_command"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Superuser created/updated successfully!${NC}"
        echo ""
        echo -e "${GREEN}Login credentials:${NC}"
        echo "Username: $username"
        echo "Password: $password"
        echo "Email: $email"
        echo ""
        echo -e "${YELLOW}Test login with:${NC}"
        echo "curl -X 'POST' 'http://localhost:8000/api/v1/auth/login' \\"
        echo "  -H 'Content-Type: application/x-www-form-urlencoded' \\"
        echo "  -d 'username=$username&password=$password'"
    else
        echo -e "${RED}❌ Failed to create superuser${NC}"
        exit 1
    fi
}

# Main script logic
main() {
    echo ""
    echo "This script will create a superuser for the RAG RBAC system."
    echo ""
    
    # Get user input or use defaults
    read -p "Enter username [$DEFAULT_USERNAME]: " username
    username=${username:-$DEFAULT_USERNAME}
    
    read -p "Enter email [$DEFAULT_EMAIL]: " email  
    email=${email:-$DEFAULT_EMAIL}
    
    read -s -p "Enter password [$DEFAULT_PASSWORD]: " password
    password=${password:-$DEFAULT_PASSWORD}
    echo ""
    
    # Confirm creation
    echo ""
    echo -e "${YELLOW}About to create superuser:${NC}"
    echo "Username: $username"
    echo "Email: $email"
    echo ""
    read -p "Continue? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        create_superuser "$username" "$email" "$password"
    else
        echo "Cancelled."
        exit 0
    fi
}

# Show help if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [--help]"
    echo ""
    echo "This script creates a superuser for the RAG RBAC system."
    echo "It will prompt for username, email, and password."
    echo ""
    echo "Default values:"
    echo "  Username: $DEFAULT_USERNAME"
    echo "  Email: $DEFAULT_EMAIL" 
    echo "  Password: $DEFAULT_PASSWORD"
    echo ""
    echo "Requirements:"
    echo "  - Docker container '$DOCKER_CONTAINER' must be running"
    echo "  - Virtual environment must be available at './venv'"
    echo "  - Must be run from the server directory"
    exit 0
fi

# Run main function
main