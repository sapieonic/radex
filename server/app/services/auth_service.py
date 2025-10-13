from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User
from app.models.user import AuthProvider
from app.schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import BadRequestException, NotFoundException, ConflictException
from app.services.firebase_service import FirebaseService
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        # Check if user with email already exists
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise ConflictException("User with this email already exists")
        
        # Check if user with username already exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise ConflictException("User with this username already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
            is_superuser=False  # Always False for API registrations - security measure
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> User:
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Check for conflicts if email or username is being updated
        if "email" in update_data:
            existing_user = self.db.query(User).filter(
                User.email == update_data["email"],
                User.id != user_id
            ).first()
            if existing_user:
                raise ConflictException("User with this email already exists")
        
        if "username" in update_data:
            existing_user = self.db.query(User).filter(
                User.username == update_data["username"],
                User.id != user_id
            ).first()
            if existing_user:
                raise ConflictException("User with this username already exists")
        
        # Hash password if it's being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def create_user_admin(self, user_data) -> User:
        """Create user with admin privileges (can set superuser status)"""
        # Check if user with email already exists
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise ConflictException("User with this email already exists")
        
        # Check if user with username already exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise ConflictException("User with this username already exists")
        
        # Create new user with admin privileges
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser  # Admin can set superuser status
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_user_admin(self, user_id: str, user_update) -> User:
        """Update user with admin privileges (can set superuser status)"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        update_data = user_update.dict(exclude_unset=True)

        # Check for conflicts if email or username is being updated
        if "email" in update_data:
            existing_user = self.db.query(User).filter(
                User.email == update_data["email"],
                User.id != user_id
            ).first()
            if existing_user:
                raise ConflictException("User with this email already exists")

        if "username" in update_data:
            existing_user = self.db.query(User).filter(
                User.username == update_data["username"],
                User.id != user_id
            ).first()
            if existing_user:
                raise ConflictException("User with this username already exists")

        # Hash password if it's being updated
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    # Firebase Authentication Methods

    def authenticate_with_firebase(self, id_token: str) -> User:
        """
        Authenticate user with Firebase ID token
        Creates a new user if they don't exist

        Args:
            id_token: Firebase ID token from the client

        Returns:
            User object

        Raises:
            ValueError: If token is invalid
        """
        try:
            # Verify the Firebase ID token
            decoded_token = FirebaseService.verify_id_token(id_token)

            firebase_uid = decoded_token.get("uid")
            email = decoded_token.get("email")

            if not firebase_uid or not email:
                raise ValueError("Invalid token: missing uid or email")

            # Check if user exists by Firebase UID
            user = self.get_user_by_firebase_uid(firebase_uid)

            if user:
                # Update existing user information
                user = self._update_user_from_firebase(user, decoded_token)
            else:
                # Create new user from Firebase token
                user = self._create_user_from_firebase(decoded_token)

            # Update last login timestamp
            user.last_login_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)

            # Set custom claims in Firebase if user is superuser
            if user.is_superuser:
                try:
                    FirebaseService.set_custom_user_claims(firebase_uid, {"superuser": True})
                except Exception as e:
                    logger.warning(f"Failed to set custom claims for superuser: {e}")

            return user

        except ValueError as e:
            logger.error(f"Firebase authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Firebase authentication: {e}")
            raise ValueError(f"Authentication failed: {str(e)}")

    def _create_user_from_firebase(self, decoded_token: Dict[str, Any]) -> User:
        """
        Create a new user from Firebase decoded token

        Args:
            decoded_token: Decoded Firebase ID token

        Returns:
            Newly created User object
        """
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        display_name = decoded_token.get("name")
        photo_url = decoded_token.get("picture")
        email_verified = decoded_token.get("email_verified", False)

        # Determine auth provider
        auth_provider = FirebaseService.extract_auth_provider(decoded_token)

        # Generate username from email or display name
        username = self._generate_unique_username(email, display_name)

        # Check if user with this email already exists (from legacy auth)
        existing_user = self.get_user_by_email(email)
        if existing_user:
            # Migrate existing user to Firebase
            existing_user.firebase_uid = firebase_uid
            existing_user.auth_provider = auth_provider
            existing_user.email_verified = email_verified
            existing_user.display_name = display_name
            existing_user.photo_url = photo_url
            self.db.commit()
            self.db.refresh(existing_user)
            logger.info(f"Migrated existing user {email} to Firebase authentication")
            return existing_user

        # Create new user
        db_user = User(
            email=email,
            username=username,
            firebase_uid=firebase_uid,
            auth_provider=auth_provider,
            display_name=display_name,
            photo_url=photo_url,
            email_verified=email_verified,
            is_active=True,
            is_superuser=False,  # New Firebase users are not superusers by default
            hashed_password=None,  # No password for Firebase users
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        logger.info(f"Created new user from Firebase: {email} (provider: {auth_provider.value})")
        return db_user

    def _update_user_from_firebase(self, user: User, decoded_token: Dict[str, Any]) -> User:
        """
        Update existing user information from Firebase token

        Args:
            user: Existing User object
            decoded_token: Decoded Firebase ID token

        Returns:
            Updated User object
        """
        # Update user information if changed
        email = decoded_token.get("email")
        display_name = decoded_token.get("name")
        photo_url = decoded_token.get("picture")
        email_verified = decoded_token.get("email_verified", False)

        # Update fields if they've changed
        if email and user.email != email:
            # Check if new email is already taken by another user
            existing_user = self.db.query(User).filter(
                User.email == email,
                User.id != user.id
            ).first()
            if not existing_user:
                user.email = email
                logger.info(f"Updated email for user {user.id} to {email}")
            else:
                logger.warning(f"Cannot update email to {email} - already taken by another user")

        if display_name:
            user.display_name = display_name

        if photo_url:
            user.photo_url = photo_url

        user.email_verified = email_verified

        # Update auth provider if needed
        new_auth_provider = FirebaseService.extract_auth_provider(decoded_token)
        if user.auth_provider != new_auth_provider:
            user.auth_provider = new_auth_provider

        self.db.commit()
        self.db.refresh(user)

        return user

    def _generate_unique_username(self, email: str, display_name: Optional[str] = None) -> str:
        """
        Generate a unique username from email or display name

        Args:
            email: User's email address
            display_name: User's display name (optional)

        Returns:
            Unique username
        """
        # Try to use display name first
        if display_name:
            base_username = display_name.lower().replace(" ", "_")
            # Remove special characters
            base_username = "".join(c for c in base_username if c.isalnum() or c == "_")
        else:
            # Use email prefix
            base_username = email.split("@")[0].lower()

        # Ensure username is unique
        username = base_username
        counter = 1

        while self.db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        return username

    def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Get user by Firebase UID

        Args:
            firebase_uid: Firebase user UID

        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.firebase_uid == firebase_uid).first()

    def sync_firebase_user(self, firebase_uid: str) -> User:
        """
        Sync user data from Firebase
        Useful for updating user information if it changed in Firebase

        Args:
            firebase_uid: Firebase user UID

        Returns:
            Updated User object

        Raises:
            NotFoundException: If user not found
        """
        user = self.get_user_by_firebase_uid(firebase_uid)
        if not user:
            raise NotFoundException(f"User with Firebase UID {firebase_uid} not found")

        try:
            # Get latest user info from Firebase
            firebase_user_info = FirebaseService.get_user_info(firebase_uid)

            # Update user fields
            if firebase_user_info.get("email") and user.email != firebase_user_info["email"]:
                # Check if new email is available
                existing = self.db.query(User).filter(
                    User.email == firebase_user_info["email"],
                    User.id != user.id
                ).first()
                if not existing:
                    user.email = firebase_user_info["email"]

            user.email_verified = firebase_user_info.get("email_verified", False)
            user.display_name = firebase_user_info.get("display_name")
            user.photo_url = firebase_user_info.get("photo_url")
            user.is_active = not firebase_user_info.get("disabled", False)

            self.db.commit()
            self.db.refresh(user)

            logger.info(f"Synced user {user.id} with Firebase data")
            return user

        except Exception as e:
            logger.error(f"Failed to sync user with Firebase: {e}")
            raise BadRequestException(f"Failed to sync user data: {str(e)}")