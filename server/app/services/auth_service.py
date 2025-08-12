from typing import Optional
from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import BadRequestException, NotFoundException, ConflictException

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
            is_superuser=user_data.is_superuser
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