from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models import Permission, Folder, User
from app.core.exceptions import PermissionDeniedException, NotFoundException
from uuid import UUID

class PermissionService:
    def __init__(self, db: Session):
        self.db = db
    
    def check_folder_permission(
        self,
        user_id: UUID,
        folder_id: UUID,
        permission_type: str = "read"
    ) -> bool:
        """Check if user has specific permission on folder"""
        # Check if user is superuser first
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_superuser:
            return True
        
        folder = self.db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise NotFoundException("Folder not found")
        
        # Owner has all permissions
        if folder.owner_id == user_id:
            return True
        
        # Check direct permissions
        permission = self.db.query(Permission).filter(
            Permission.user_id == user_id,
            Permission.folder_id == folder_id
        ).first()
        
        if permission:
            if permission.is_admin:
                return True
            if permission_type == "read" and permission.can_read:
                return True
            if permission_type == "write" and permission.can_write:
                return True
            if permission_type == "delete" and permission.can_delete:
                return True
        
        # Check parent folder permissions (inheritance)
        if folder.parent_id:
            return self.check_folder_permission(user_id, folder.parent_id, permission_type)
        
        return False
    
    def get_user_accessible_folders(self, user_id: UUID) -> List[Folder]:
        """Get all folders accessible to user"""
        # Check if user is superuser first
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_superuser:
            # Superuser can access all folders
            return self.db.query(Folder).all()
        
        # Get folders owned by user
        owned_folders = self.db.query(Folder).filter(Folder.owner_id == user_id).all()
        
        # Get folders with explicit permissions
        permissions = self.db.query(Permission).filter(
            Permission.user_id == user_id,
            or_(
                Permission.can_read == True,
                Permission.can_write == True,
                Permission.can_delete == True,
                Permission.is_admin == True
            )
        ).all()
        
        permitted_folder_ids = [p.folder_id for p in permissions]
        permitted_folders = self.db.query(Folder).filter(
            Folder.id.in_(permitted_folder_ids)
        ).all() if permitted_folder_ids else []
        
        # Combine and deduplicate
        all_folders = owned_folders + permitted_folders
        unique_folders = {f.id: f for f in all_folders}
        
        return list(unique_folders.values())
    
    def grant_permission(
        self,
        granter_id: UUID,
        user_id: UUID,
        folder_id: UUID,
        can_read: bool = False,
        can_write: bool = False,
        can_delete: bool = False,
        is_admin: bool = False
    ) -> Permission:
        """Grant permission to user for folder"""
        # Check if granter is superuser
        granter = self.db.query(User).filter(User.id == granter_id).first()
        if not (granter and granter.is_superuser):
            # If not superuser, check if granter has admin rights
            if not self.check_folder_permission(granter_id, folder_id, "admin"):
                folder = self.db.query(Folder).filter(Folder.id == folder_id).first()
                if not folder or folder.owner_id != granter_id:
                    raise PermissionDeniedException("You don't have permission to grant access to this folder")
        
        # Check if permission already exists
        existing_permission = self.db.query(Permission).filter(
            Permission.user_id == user_id,
            Permission.folder_id == folder_id
        ).first()
        
        if existing_permission:
            # Update existing permission
            existing_permission.can_read = can_read
            existing_permission.can_write = can_write
            existing_permission.can_delete = can_delete
            existing_permission.is_admin = is_admin
            existing_permission.granted_by = granter_id
        else:
            # Create new permission
            existing_permission = Permission(
                user_id=user_id,
                folder_id=folder_id,
                can_read=can_read,
                can_write=can_write,
                can_delete=can_delete,
                is_admin=is_admin,
                granted_by=granter_id
            )
            self.db.add(existing_permission)
        
        self.db.commit()
        self.db.refresh(existing_permission)
        return existing_permission
    
    def revoke_permission(
        self,
        revoker_id: UUID,
        user_id: UUID,
        folder_id: UUID
    ) -> bool:
        """Revoke user's permission for folder"""
        # Check if revoker is superuser
        revoker = self.db.query(User).filter(User.id == revoker_id).first()
        if not (revoker and revoker.is_superuser):
            # If not superuser, check if revoker has admin rights
            folder = self.db.query(Folder).filter(Folder.id == folder_id).first()
            if not folder:
                raise NotFoundException("Folder not found")
            
            if folder.owner_id != revoker_id and not self.check_folder_permission(revoker_id, folder_id, "admin"):
                raise PermissionDeniedException("You don't have permission to revoke access to this folder")
        
        permission = self.db.query(Permission).filter(
            Permission.user_id == user_id,
            Permission.folder_id == folder_id
        ).first()
        
        if permission:
            self.db.delete(permission)
            self.db.commit()
            return True
        
        return False
    
    def get_folder_permissions(self, folder_id: UUID) -> List[Permission]:
        """Get all permissions for a folder"""
        return self.db.query(Permission).filter(
            Permission.folder_id == folder_id
        ).all()
    
    def check_folder_access(self, user_id: UUID, folder_id: UUID, permission_type: str = "read"):
        """Check folder access and raise exception if denied"""
        if not self.check_folder_permission(user_id, folder_id, permission_type):
            raise PermissionDeniedException(f"You don't have {permission_type} permission for this folder")