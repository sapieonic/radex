from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app.core.security import decode_access_token
from app.models import User
from app.schemas import TokenData
from app.services.firebase_service import FirebaseService
import logging

logger = logging.getLogger(__name__)

# Use HTTPBearer for Firebase ID tokens
http_bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from Firebase ID token

    This function verifies the Firebase ID token and returns the corresponding user.
    If the user doesn't exist, they will be automatically created.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        # Verify Firebase ID token
        decoded_token = FirebaseService.verify_id_token(token)
        firebase_uid = decoded_token.get("uid")

        if not firebase_uid:
            raise credentials_exception

        # Get user by Firebase UID
        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

        if user is None:
            # User not found - this shouldn't happen if they authenticated through Firebase login
            # but we'll handle it gracefully
            logger.warning(f"User with Firebase UID {firebase_uid} not found in database")
            raise credentials_exception

        return user

    except ValueError as e:
        # Firebase token verification failed
        logger.error(f"Firebase token verification failed: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error validating credentials: {e}")
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user