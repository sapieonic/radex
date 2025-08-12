from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    FolderCreate, FolderUpdate, Folder, FolderWithPermissions,
    PermissionGrant, PermissionInfo
)
from app.models import Folder as FolderModel, User as UserModel
from app.core.dependencies import get_current_active_user
from app.core.exceptions import NotFoundException, ConflictException, PermissionDeniedException
from app.services.permission_service import PermissionService

router = APIRouter()

def build_folder_path(db: Session, parent_id: UUID = None, folder_name: str = "") -> str:
    """Build the full path for a folder"""
    if not parent_id:
        return f"/{folder_name}"
    
    parent = db.query(FolderModel).filter(FolderModel.id == parent_id).first()
    if parent:
        return f"{parent.path}/{folder_name}"
    return f"/{folder_name}"

@router.get("/", response_model=List[FolderWithPermissions])
def list_folders(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all folders accessible to the current user"""
    permission_service = PermissionService(db)
    folders = permission_service.get_user_accessible_folders(current_user.id)
    
    # Add permission information to each folder
    folders_with_permissions = []
    for folder in folders:
        folder_dict = {
            "id": folder.id,
            "name": folder.name,
            "parent_id": folder.parent_id,
            "owner_id": folder.owner_id,
            "path": folder.path,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
            "can_read": True,  # If they can see it, they can read it
            "can_write": permission_service.check_folder_permission(current_user.id, folder.id, "write"),
            "can_delete": permission_service.check_folder_permission(current_user.id, folder.id, "delete"),
            "is_admin": folder.owner_id == current_user.id or permission_service.check_folder_permission(current_user.id, folder.id, "admin")
        }
        folders_with_permissions.append(FolderWithPermissions(**folder_dict))
    
    return folders_with_permissions

@router.post("/", response_model=Folder, status_code=status.HTTP_201_CREATED)
def create_folder(
    folder_data: FolderCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new folder"""
    permission_service = PermissionService(db)
    
    # If parent folder is specified, check write permission
    if folder_data.parent_id:
        permission_service.check_folder_access(current_user.id, folder_data.parent_id, "write")
        
        # Check if folder with same name exists in parent
        existing = db.query(FolderModel).filter(
            FolderModel.name == folder_data.name,
            FolderModel.parent_id == folder_data.parent_id
        ).first()
        if existing:
            raise ConflictException("Folder with this name already exists in the parent folder")
    else:
        # Check if root folder with same name exists for this user
        existing = db.query(FolderModel).filter(
            FolderModel.name == folder_data.name,
            FolderModel.parent_id == None,
            FolderModel.owner_id == current_user.id
        ).first()
        if existing:
            raise ConflictException("Root folder with this name already exists")
    
    # Build folder path
    folder_path = build_folder_path(db, folder_data.parent_id, folder_data.name)
    
    # Create folder
    new_folder = FolderModel(
        name=folder_data.name,
        parent_id=folder_data.parent_id,
        owner_id=current_user.id,
        path=folder_path
    )
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)
    
    return new_folder

@router.get("/{folder_id}", response_model=FolderWithPermissions)
def get_folder(
    folder_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get folder details"""
    permission_service = PermissionService(db)
    permission_service.check_folder_access(current_user.id, folder_id, "read")
    
    folder = db.query(FolderModel).filter(FolderModel.id == folder_id).first()
    if not folder:
        raise NotFoundException("Folder not found")
    
    folder_dict = {
        "id": folder.id,
        "name": folder.name,
        "parent_id": folder.parent_id,
        "owner_id": folder.owner_id,
        "path": folder.path,
        "created_at": folder.created_at,
        "updated_at": folder.updated_at,
        "can_read": True,
        "can_write": permission_service.check_folder_permission(current_user.id, folder.id, "write"),
        "can_delete": permission_service.check_folder_permission(current_user.id, folder.id, "delete"),
        "is_admin": folder.owner_id == current_user.id or permission_service.check_folder_permission(current_user.id, folder.id, "admin")
    }
    
    return FolderWithPermissions(**folder_dict)

@router.put("/{folder_id}", response_model=Folder)
def update_folder(
    folder_id: UUID,
    folder_update: FolderUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update folder"""
    permission_service = PermissionService(db)
    permission_service.check_folder_access(current_user.id, folder_id, "write")
    
    folder = db.query(FolderModel).filter(FolderModel.id == folder_id).first()
    if not folder:
        raise NotFoundException("Folder not found")
    
    if folder_update.name:
        # Check if folder with new name exists in same parent
        existing = db.query(FolderModel).filter(
            FolderModel.name == folder_update.name,
            FolderModel.parent_id == folder.parent_id,
            FolderModel.id != folder_id
        ).first()
        if existing:
            raise ConflictException("Folder with this name already exists in the parent folder")
        
        folder.name = folder_update.name
        folder.path = build_folder_path(db, folder.parent_id, folder_update.name)
    
    db.commit()
    db.refresh(folder)
    
    return folder

@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete folder and all its contents"""
    permission_service = PermissionService(db)
    permission_service.check_folder_access(current_user.id, folder_id, "delete")
    
    folder = db.query(FolderModel).filter(FolderModel.id == folder_id).first()
    if not folder:
        raise NotFoundException("Folder not found")
    
    db.delete(folder)
    db.commit()

@router.post("/{folder_id}/permissions", response_model=PermissionInfo, status_code=status.HTTP_201_CREATED)
def grant_folder_permission(
    folder_id: UUID,
    permission_grant: PermissionGrant,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Grant permission to a user for a folder"""
    permission_service = PermissionService(db)
    
    permission = permission_service.grant_permission(
        granter_id=current_user.id,
        user_id=permission_grant.user_id,
        folder_id=folder_id,
        can_read=permission_grant.can_read,
        can_write=permission_grant.can_write,
        can_delete=permission_grant.can_delete,
        is_admin=permission_grant.is_admin
    )
    
    return permission

@router.get("/{folder_id}/permissions", response_model=List[PermissionInfo])
def list_folder_permissions(
    folder_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all permissions for a folder"""
    permission_service = PermissionService(db)
    
    # Check if user has admin access to the folder
    folder = db.query(FolderModel).filter(FolderModel.id == folder_id).first()
    if not folder:
        raise NotFoundException("Folder not found")
    
    if folder.owner_id != current_user.id and not permission_service.check_folder_permission(current_user.id, folder_id, "admin"):
        raise PermissionDeniedException("You don't have permission to view folder permissions")
    
    permissions = permission_service.get_folder_permissions(folder_id)
    return permissions

@router.delete("/{folder_id}/permissions/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_folder_permission(
    folder_id: UUID,
    user_id: UUID,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a user's permission for a folder"""
    permission_service = PermissionService(db)
    
    success = permission_service.revoke_permission(
        revoker_id=current_user.id,
        user_id=user_id,
        folder_id=folder_id
    )
    
    if not success:
        raise NotFoundException("Permission not found")