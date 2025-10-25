from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.schemas import UserCreate, User, Token, UserLogin
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.core.dependencies import get_current_active_user
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class AuthConfigResponse(BaseModel):
    """Response model for authentication configuration"""
    enable_google_login: bool
    enable_microsoft_login: bool
    enable_okta_login: bool
    enable_manual_signup: bool


class FirebaseTokenRequest(BaseModel):
    """Request model for Firebase authentication"""
    id_token: str


class FirebaseAuthResponse(BaseModel):
    """Response model for Firebase authentication"""
    user: User
    access_token: str
    token_type: str = "bearer"


@router.get("/config", response_model=AuthConfigResponse)
def get_auth_config():
    """
    Get authentication configuration

    Returns which authentication methods are enabled on the server.
    This allows the frontend to conditionally show/hide login options.
    """
    return AuthConfigResponse(
        enable_google_login=settings.enable_google_login,
        enable_microsoft_login=settings.enable_microsoft_login,
        enable_okta_login=settings.enable_okta_login,
        enable_manual_signup=settings.enable_manual_signup
    )


@router.post("/firebase/login", response_model=User)
def firebase_login(
    token_request: FirebaseTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Firebase ID token

    This endpoint accepts a Firebase ID token from the client, verifies it,
    and either creates a new user or updates an existing user's information.
    Returns the user object with their information.
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.authenticate_with_firebase(token_request.id_token)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        logger.info(f"User {user.email} authenticated successfully via Firebase")
        return user

    except ValueError as e:
        logger.warning(f"Firebase authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during Firebase authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user (Legacy - for backward compatibility)"""
    auth_service = AuthService(db)
    user = auth_service.create_user(user_data)
    return user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and receive access token"""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user account and all associated data"""
    auth_service = AuthService(db)
    auth_service.delete_user(str(current_user.id))
    return None