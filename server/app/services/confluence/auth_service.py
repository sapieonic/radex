from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
import base64
import os
import uuid

from app.models import ConfluenceCredential, ConfluenceType, User
from app.config import settings
from app.core.exceptions import BadRequestException, NotFoundException


class ConfluenceAuthService:
    def __init__(self, db: Session):
        self.db = db
        self._cipher_suite = self._get_cipher_suite()
    
    def _get_cipher_suite(self) -> Fernet:
        """Get or create encryption cipher"""
        key = os.environ.get("CONFLUENCE_ENCRYPTION_KEY")
        if not key:
            # Generate a key if not provided (for development)
            key = Fernet.generate_key().decode()
            os.environ["CONFLUENCE_ENCRYPTION_KEY"] = key
        return Fernet(key)
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage"""
        if not token:
            return None
        return self._cipher_suite.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token"""
        if not encrypted_token:
            return None
        try:
            return self._cipher_suite.decrypt(encrypted_token.encode()).decode()
        except Exception:
            # If decryption fails (e.g., key changed), return None
            # This will cause the credential to be marked as invalid
            return None
    
    def create_or_update_credential(
        self,
        user_id: uuid.UUID,
        confluence_type: ConfluenceType,
        base_url: str,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        oauth_token: Optional[str] = None,
        oauth_refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None
    ) -> ConfluenceCredential:
        """Create or update Confluence credentials for a user"""
        
        # Check if credential already exists
        existing = self.db.query(ConfluenceCredential).filter(
            ConfluenceCredential.user_id == user_id,
            ConfluenceCredential.base_url == base_url
        ).first()
        
        if existing:
            # Update existing credential
            existing.confluence_type = confluence_type
            existing.email = email
            if api_token:
                existing.api_token_encrypted = self._encrypt_token(api_token)
            if oauth_token:
                existing.oauth_token_encrypted = self._encrypt_token(oauth_token)
            if oauth_refresh_token:
                existing.oauth_refresh_token_encrypted = self._encrypt_token(oauth_refresh_token)
            if token_expires_at:
                existing.token_expires_at = token_expires_at
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new credential
            credential = ConfluenceCredential(
                user_id=user_id,
                confluence_type=confluence_type,
                base_url=base_url,
                email=email,
                api_token_encrypted=self._encrypt_token(api_token) if api_token else None,
                oauth_token_encrypted=self._encrypt_token(oauth_token) if oauth_token else None,
                oauth_refresh_token_encrypted=self._encrypt_token(oauth_refresh_token) if oauth_refresh_token else None,
                token_expires_at=token_expires_at
            )
            
            self.db.add(credential)
            self.db.commit()
            self.db.refresh(credential)
            return credential
    
    def get_credential(self, credential_id: uuid.UUID, user_id: uuid.UUID) -> ConfluenceCredential:
        """Get a credential by ID, ensuring it belongs to the user"""
        credential = self.db.query(ConfluenceCredential).filter(
            ConfluenceCredential.id == credential_id,
            ConfluenceCredential.user_id == user_id
        ).first()
        
        if not credential:
            raise NotFoundException("Confluence credential not found")
        
        return credential
    
    def get_user_credentials(self, user_id: uuid.UUID) -> list[ConfluenceCredential]:
        """Get all Confluence credentials for a user"""
        return self.db.query(ConfluenceCredential).filter(
            ConfluenceCredential.user_id == user_id
        ).all()
    
    def delete_credential(self, credential_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a credential"""
        credential = self.get_credential(credential_id, user_id)
        self.db.delete(credential)
        self.db.commit()
        return True
    
    def get_decrypted_tokens(self, credential: ConfluenceCredential) -> Dict[str, Optional[str]]:
        """Get decrypted tokens from a credential"""
        return {
            "api_token": self._decrypt_token(credential.api_token_encrypted),
            "oauth_token": self._decrypt_token(credential.oauth_token_encrypted),
            "oauth_refresh_token": self._decrypt_token(credential.oauth_refresh_token_encrypted)
        }
    
    def refresh_oauth_token(
        self,
        credential: ConfluenceCredential,
        new_token: str,
        new_refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ) -> ConfluenceCredential:
        """Update OAuth tokens after refresh"""
        credential.oauth_token_encrypted = self._encrypt_token(new_token)
        
        if new_refresh_token:
            credential.oauth_refresh_token_encrypted = self._encrypt_token(new_refresh_token)
        
        if expires_in:
            credential.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        self.db.commit()
        self.db.refresh(credential)
        return credential
    
    def validate_credential(self, credential: ConfluenceCredential) -> bool:
        """Validate if a credential is still valid"""
        if credential.confluence_type == ConfluenceType.CLOUD:
            # Check OAuth token expiration
            if credential.token_expires_at and credential.token_expires_at < datetime.utcnow():
                return False
        elif credential.confluence_type in [ConfluenceType.SERVER, ConfluenceType.DATA_CENTER]:
            # API tokens don't expire, but check if it exists
            if not credential.api_token_encrypted:
                return False
        
        return True