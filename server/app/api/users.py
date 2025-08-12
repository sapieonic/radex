from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import User, UserCreate, UserUpdate
from pydantic import BaseModel, EmailStr, Field
from app.models import User as UserModel
from app.core.dependencies import get_current_superuser, get_current_active_user
from app.services.auth_service import AuthService
from app.core.exceptions import NotFoundException, BadRequestException

# Admin-specific schemas for CRUD operations
class AdminUserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    is_active: bool = True
    is_superuser: bool = False

class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

router = APIRouter()

@router.get("/find", response_model=User)
async def find_user(
    email: Optional[str] = Query(None, description="Find user by exact email"),
    username: Optional[str] = Query(None, description="Find user by exact username"),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Find a user by exact email or username. Available to all authenticated users.
    
    This endpoint is designed for sharing purposes - to find specific users to share 
    folders or grant permissions to. Only one of email or username should be provided.
    """
    if not email and not username:
        raise BadRequestException("Either email or username must be provided")
    
    if email and username:
        raise BadRequestException("Provide either email or username, not both")
    
    auth_service = AuthService(db)
    
    if email:
        user = auth_service.get_user_by_email(email)
    else:
        user = auth_service.get_user_by_username(username)
    
    if not user:
        raise NotFoundException("User not found")
    
    # Only return active users to regular users (privacy/security)
    if not user.is_active and not current_user.is_superuser:
        raise NotFoundException("User not found")
    
    user_dict = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    return User(**user_dict)

@router.get("/", response_model=List[User])
async def list_users(
    email: Optional[str] = Query(None, description="Filter by email address"),
    username: Optional[str] = Query(None, description="Filter by username"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_superuser: Optional[bool] = Query(None, description="Filter by superuser status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    List users with optional filtering. Only accessible to superusers.
    
    Query parameters:
    - email: Exact email match
    - username: Exact username match  
    - is_active: Filter by active status
    - is_superuser: Filter by superuser status
    - limit: Maximum number of results (1-100, default 50)
    - offset: Number of results to skip (pagination)
    """
    auth_service = AuthService(db)
    
    # Build query
    query = db.query(UserModel)
    
    # Apply filters
    if email:
        query = query.filter(UserModel.email == email)
    if username:
        query = query.filter(UserModel.username == username)
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    if is_superuser is not None:
        query = query.filter(UserModel.is_superuser == is_superuser)
    
    # Apply pagination
    users = query.offset(offset).limit(limit).all()
    
    # Convert to User schema (which excludes sensitive fields)
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        user_list.append(User(**user_dict))
    
    return user_list

@router.get("/search", response_model=List[User])
async def search_users(
    q: str = Query(..., min_length=2, description="Search term for email or username"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Search users by email or username (partial match). Only accessible to superusers.
    
    The search term will be matched against both email and username fields using LIKE.
    """
    # Search in both email and username fields
    from sqlalchemy import or_
    users = db.query(UserModel).filter(
        or_(
            UserModel.email.ilike(f"%{q}%"),
            UserModel.username.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    # Convert to User schema
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        user_list.append(User(**user_dict))
    
    return user_list

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: UUID,
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID. Only accessible to superusers."""
    auth_service = AuthService(db)
    
    user = auth_service.get_user_by_id(str(user_id))
    if not user:
        raise NotFoundException("User not found")
    
    user_dict = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    return User(**user_dict)

# CRUD Operations (Superuser only)

@router.post("/", response_model=User, status_code=201)
async def create_user(
    user_data: AdminUserCreate,
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Create a new user. Only accessible to superusers."""
    auth_service = AuthService(db)
    
    # Create user with admin privileges (can set superuser status)
    new_user = auth_service.create_user_admin(user_data)
    
    user_dict = {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "is_active": new_user.is_active,
        "is_superuser": new_user.is_superuser,
        "created_at": new_user.created_at,
        "updated_at": new_user.updated_at
    }
    
    return User(**user_dict)

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: UUID,
    user_update: AdminUserUpdate,
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Update a user. Only accessible to superusers."""
    auth_service = AuthService(db)
    
    # Check if user exists
    user = auth_service.get_user_by_id(str(user_id))
    if not user:
        raise NotFoundException("User not found")
    
    # Update user
    updated_user = auth_service.update_user_admin(str(user_id), user_update)
    
    user_dict = {
        "id": updated_user.id,
        "email": updated_user.email,
        "username": updated_user.username,
        "is_active": updated_user.is_active,
        "is_superuser": updated_user.is_superuser,
        "created_at": updated_user.created_at,
        "updated_at": updated_user.updated_at
    }
    
    return User(**user_dict)

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: UserModel = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Delete a user. Only accessible to superusers."""
    auth_service = AuthService(db)
    
    # Check if user exists
    user = auth_service.get_user_by_id(str(user_id))
    if not user:
        raise NotFoundException("User not found")
    
    # Prevent self-deletion
    if str(user_id) == str(current_user.id):
        raise BadRequestException("Cannot delete your own account")
    
    # Delete user
    success = auth_service.delete_user(str(user_id))
    if not success:
        raise NotFoundException("User not found")
    
    return None

