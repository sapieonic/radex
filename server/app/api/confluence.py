from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models import User, ConfluenceImport, ImportType
from app.schemas.confluence import (
    ConfluenceAuthRequest,
    ConfluenceAuthResponse,
    ConfluenceCredentialList,
    ConfluenceImportRequest,
    ConfluenceImportResponse,
    ConfluenceImportStatus,
    ConfluenceSearchRequest,
    ConfluenceSearchResult,
    ConfluenceSpace,
    ConfluencePage,
    ConfluenceSyncRequest,
    ConfluenceSyncResponse,
    ConfluenceBatchImportRequest,
    ConfluenceBatchImportResponse
)
from app.core.dependencies import get_current_user
from app.services.confluence import (
    ConfluenceAuthService,
    ConfluenceClient,
    ConfluenceImportService
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter(tags=["confluence"])


# Authentication Endpoints
@router.post("/auth", response_model=ConfluenceAuthResponse)
def authenticate_confluence(
    request: ConfluenceAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Authenticate with Confluence and store credentials"""
    auth_service = ConfluenceAuthService(db)
    
    # Create or update credential
    credential = auth_service.create_or_update_credential(
        user_id=current_user.id,
        confluence_type=request.confluence_type,
        base_url=request.base_url,
        email=request.email,
        api_token=request.api_token,
        oauth_token=request.oauth_token,
        oauth_refresh_token=request.oauth_refresh_token,
        token_expires_at=request.token_expires_at
    )
    
    # Test connection
    client = ConfluenceClient(credential, auth_service)
    is_valid = client.test_connection()
    
    return ConfluenceAuthResponse(
        id=credential.id,
        confluence_type=credential.confluence_type,
        base_url=credential.base_url,
        email=credential.email,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
        is_valid=is_valid
    )


@router.get("/auth", response_model=ConfluenceCredentialList)
def get_confluence_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all Confluence credentials for the current user"""
    auth_service = ConfluenceAuthService(db)
    credentials = auth_service.get_user_credentials(current_user.id)
    
    response_credentials = []
    for cred in credentials:
        client = ConfluenceClient(cred, auth_service)
        is_valid = client.test_connection()
        
        response_credentials.append(ConfluenceAuthResponse(
            id=cred.id,
            confluence_type=cred.confluence_type,
            base_url=cred.base_url,
            email=cred.email,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
            is_valid=is_valid
        ))
    
    return ConfluenceCredentialList(credentials=response_credentials)


@router.get("/auth/status/{credential_id}")
def check_auth_status(
    credential_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a Confluence credential is still valid"""
    auth_service = ConfluenceAuthService(db)
    
    try:
        credential = auth_service.get_credential(credential_id, current_user.id)
        client = ConfluenceClient(credential, auth_service)
        is_valid = client.test_connection()
        
        return {"credential_id": credential_id, "is_valid": is_valid}
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Credential not found")


@router.delete("/auth/{credential_id}")
def delete_confluence_credential(
    credential_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a Confluence credential"""
    auth_service = ConfluenceAuthService(db)
    
    try:
        auth_service.delete_credential(credential_id, current_user.id)
        return {"message": "Credential deleted successfully"}
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Credential not found")


# Content Discovery Endpoints
@router.get("/spaces", response_model=List[ConfluenceSpace])
def get_confluence_spaces(
    credential_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available Confluence spaces"""
    auth_service = ConfluenceAuthService(db)
    
    try:
        credential = auth_service.get_credential(credential_id, current_user.id)
        client = ConfluenceClient(credential, auth_service)
        
        spaces = client.get_spaces()
        
        return [
            ConfluenceSpace(
                key=space['key'],
                name=space['name'],
                description=space.get('description', {}).get('plain', {}).get('value'),
                homepage_id=space.get('homepage', {}).get('id')
            )
            for space in spaces
        ]
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Credential not found")
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/spaces/{space_key}/pages", response_model=List[ConfluencePage])
def get_space_pages(
    credential_id: UUID,
    space_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pages in a Confluence space"""
    auth_service = ConfluenceAuthService(db)
    
    try:
        credential = auth_service.get_credential(credential_id, current_user.id)
        client = ConfluenceClient(credential, auth_service)
        
        pages = client.get_space_content(space_key)
        
        return [
            ConfluencePage(
                id=page['id'],
                title=page['title'],
                space_key=space_key,
                parent_id=page.get('ancestors', [{}])[-1].get('id') if page.get('ancestors') else None,
                version=page.get('version', {}).get('number', 0),
                created_date=page.get('history', {}).get('createdDate'),
                modified_date=page.get('version', {}).get('when'),
                has_children=page.get('children', {}).get('page', {}).get('size', 0) > 0,
                has_attachments=page.get('children', {}).get('attachment', {}).get('size', 0) > 0
            )
            for page in pages
        ]
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Credential not found")
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search", response_model=List[ConfluenceSearchResult])
def search_confluence(
    request: ConfluenceSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search Confluence content"""
    auth_service = ConfluenceAuthService(db)
    
    try:
        credential = auth_service.get_credential(request.credential_id, current_user.id)
        client = ConfluenceClient(credential, auth_service)
        
        # Convert text search to CQL if needed
        if request.search_type == "text":
            cql = f'text ~ "{request.query}"'
        else:
            cql = request.query
        
        results = client.search_content(cql, limit=request.limit)
        
        return [
            ConfluenceSearchResult(
                id=result['id'],
                title=result['title'],
                space_key=result.get('space', {}).get('key', ''),
                space_name=result.get('space', {}).get('name', ''),
                excerpt=result.get('excerpt', ''),
                url=result.get('_links', {}).get('webui'),
                last_modified=result.get('version', {}).get('when')
            )
            for result in results
        ]
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Credential not found")
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))


# Import Endpoints
@router.post("/import", response_model=ConfluenceImportResponse)
def create_import_job(
    request: ConfluenceImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new Confluence import job"""
    import_service = ConfluenceImportService(db)
    
    try:
        # Create import job
        import_job = import_service.create_import_job(
            user=current_user,
            credential_id=request.credential_id,
            folder_id=request.folder_id,
            import_type=request.import_type,
            space_key=request.space_key,
            page_id=request.page_id,
            metadata={
                "include_attachments": request.include_attachments,
                "include_comments": request.include_comments,
                "recursive": request.recursive
            }
        )
        
        # Process import in background
        background_tasks.add_task(
            import_service.process_import,
            import_job.id,
            request.include_attachments,
            request.include_comments
        )
        
        return ConfluenceImportResponse(
            id=import_job.id,
            import_type=import_job.import_type,
            sync_status=import_job.sync_status,
            total_pages=import_job.total_pages,
            processed_pages=import_job.processed_pages,
            error_message=import_job.error_message,
            created_at=import_job.created_at,
            last_sync_at=import_job.last_sync_at
        )
        
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/import/{import_id}/status", response_model=ConfluenceImportStatus)
def get_import_status(
    import_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the status of an import job"""
    import_service = ConfluenceImportService(db)
    
    try:
        status = import_service.get_import_status(import_id)
        
        # Verify the import belongs to the user
        import_job = db.query(ConfluenceImport).filter(
            ConfluenceImport.id == import_id
        ).first()
        
        if not import_job:
            raise NotFoundException("Import job not found")
        
        # Check if user has access to the folder
        from app.services.permission_service import PermissionService
        permission_service = PermissionService(db)
        
        if not permission_service.check_folder_permission(current_user.id, import_job.folder_id, "read"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ConfluenceImportStatus(**status)
        
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/import/batch", response_model=ConfluenceBatchImportResponse)
def create_batch_import(
    request: ConfluenceBatchImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple import jobs at once"""
    import_service = ConfluenceImportService(db)
    
    job_ids = []
    
    try:
        for import_item in request.imports:
            import_job = import_service.create_import_job(
                user=current_user,
                credential_id=request.credential_id,
                folder_id=request.folder_id,
                import_type=import_item.get('import_type'),
                space_key=import_item.get('space_key'),
                page_id=import_item.get('page_id')
            )
            
            job_ids.append(import_job.id)
            
            # Process each import in background
            background_tasks.add_task(
                import_service.process_import,
                import_job.id,
                True,  # include_attachments
                False  # include_comments
            )
        
        return ConfluenceBatchImportResponse(
            job_ids=job_ids,
            total_jobs=len(job_ids),
            status="Processing"
        )
        
    except (NotFoundException, BadRequestException) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


# Sync Endpoints
@router.post("/sync/{import_id}")
def sync_confluence_content(
    import_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync an existing import with latest Confluence content"""
    import_service = ConfluenceImportService(db)
    
    # Get import job
    import_job = db.query(ConfluenceImport).filter(
        ConfluenceImport.id == import_id
    ).first()
    
    if not import_job:
        raise HTTPException(status_code=404, detail="Import job not found")
    
    # Check permissions
    from app.services.permission_service import PermissionService
    permission_service = PermissionService(db)
    
    if not permission_service.check_folder_permission(current_user.id, import_job.folder_id, "write"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Process sync in background
    background_tasks.add_task(
        import_service.process_import,
        import_id,
        True,  # include_attachments
        False  # include_comments
    )
    
    return {"message": "Sync started", "import_id": import_id}


@router.get("/sync/history")
def get_sync_history(
    folder_id: Optional[UUID] = None,
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync history for user's imports"""
    query = db.query(ConfluenceImport).join(ConfluenceImport.folder)
    
    if folder_id:
        query = query.filter(ConfluenceImport.folder_id == folder_id)
    
    # Filter by user's folders
    from app.models import Folder
    from app.services.permission_service import PermissionService
    permission_service = PermissionService(db)
    
    user_folders = db.query(Folder).filter(Folder.owner_id == current_user.id).all()
    accessible_folder_ids = [
        f.id for f in user_folders 
        if permission_service.check_folder_permission(current_user.id, f.id, "read")
    ]
    
    query = query.filter(ConfluenceImport.folder_id.in_(accessible_folder_ids))
    
    imports = query.order_by(ConfluenceImport.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": imp.id,
            "import_type": imp.import_type,
            "sync_status": imp.sync_status,
            "total_pages": imp.total_pages,
            "processed_pages": imp.processed_pages,
            "folder_id": imp.folder_id,
            "space_key": imp.space_key,
            "page_id": imp.page_id,
            "created_at": imp.created_at,
            "last_sync_at": imp.last_sync_at,
            "error_message": imp.error_message
        }
        for imp in imports
    ]