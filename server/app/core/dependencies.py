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
    Get current user from either Firebase ID token or legacy JWT token

    This function first tries to verify as a Firebase token, and if that fails,
    falls back to legacy JWT verification for backward compatibility.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    # Try Firebase ID token first
    try:
        decoded_token = FirebaseService.verify_id_token(token)
        firebase_uid = decoded_token.get("uid")

        if firebase_uid:
            # Get user by Firebase UID
            user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

            if user is None:
                logger.warning(f"User with Firebase UID {firebase_uid} not found in database")
                raise credentials_exception

            return user
    except Exception as e:
        # Firebase token verification failed, try legacy JWT
        logger.debug(f"Firebase token verification failed: {e}, trying legacy JWT")
        pass

    # Fallback to legacy JWT token verification
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id)
    except JWTError as e:
        logger.error(f"JWT token verification failed: {e}")
        raise credentials_exception

    # Get user by ID (legacy JWT uses user ID)
    user = db.query(User).filter(User.id == token_data.user_id).first()

    if user is None:
        logger.warning(f"User with ID {token_data.user_id} not found in database")
        raise credentials_exception

    return user

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