"""
File Sync/Import API Endpoints

Handles importing files from external providers (SharePoint/OneDrive) into RADEX.
Files are downloaded to temp storage, uploaded to MinIO, and processed through
the existing document ingestion pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import tempfile
import os
from pathlib import Path

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.folder import Folder
from app.models.document import Document
from app.models.provider_connection import ProviderConnection
from app.models.provider_item_ref import ProviderItemRef, ProviderType
from app.schemas.sharepoint import (
    SyncImportRequest,
    SyncImportResponse,
    SyncedItemInfo,
    SharePointItemToSync,
)
from app.services.microsoft_graph_service import MicrosoftGraphService
from app.services.document_service import DocumentService
from app.services.permission_service import PermissionService
from app.core.exceptions import BadRequestException, NotFoundException, PermissionDeniedException
from app.config import settings

router = APIRouter(
    prefix="/sync",
    tags=["File Sync"],
)


@router.post("/import", response_model=SyncImportResponse)
async def import_from_sharepoint(
    request: SyncImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Import files from SharePoint/OneDrive into RADEX.

    **Process:**
    1. Downloads files from SharePoint to temporary storage
    2. Uploads to MinIO using existing document service
    3. Triggers embedding generation pipeline
    4. Stores provider references for idempotency
    5. Cleans up temporary files

    **Idempotency:** Files already synced (based on drive_id + item_id) are skipped.

    Args:
        request: Sync request with connection ID, folder ID, and items to sync

    Returns:
        Sync results with counts and per-item status
    """
    # Validate connection belongs to user
    connection = (
        db.query(ProviderConnection)
        .filter(
            ProviderConnection.id == request.connection_id,
            ProviderConnection.user_id == current_user.id,
        )
        .first()
    )

    if not connection:
        raise NotFoundException("Connection not found or access denied")

    # Validate target folder exists and user has write permission
    folder = db.query(Folder).filter(Folder.id == request.folder_id).first()
    if not folder:
        raise NotFoundException("Target folder not found")

    permission_service = PermissionService(db)
    if not permission_service.check_folder_access(current_user.id, folder.id, "write"):
        raise PermissionDeniedException("You don't have write access to this folder")

    # Initialize services
    graph_service = MicrosoftGraphService(db)
    document_service = DocumentService(db)

    # Track results
    results: List[SyncedItemInfo] = []
    succeeded = 0
    skipped = 0
    failed = 0

    # Process each item
    for item in request.items:
        try:
            result = await _sync_single_item(
                db=db,
                connection=connection,
                folder=folder,
                item=item,
                current_user=current_user,
                graph_service=graph_service,
                document_service=document_service,
            )

            results.append(result)

            if result.status == "success":
                succeeded += 1
            elif result.status == "skipped":
                skipped += 1
            else:
                failed += 1

        except Exception as e:
            # Log error and continue with next item
            results.append(
                SyncedItemInfo(
                    sharepoint_item_id=item.item_id,
                    document_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
                    filename="Unknown",
                    status="failed",
                    message=str(e),
                )
            )
            failed += 1

    return SyncImportResponse(
        total=len(request.items),
        succeeded=succeeded,
        skipped=skipped,
        failed=failed,
        results=results,
    )


async def _sync_single_item(
    db: Session,
    connection: ProviderConnection,
    folder: Folder,
    item: SharePointItemToSync,
    current_user: User,
    graph_service: MicrosoftGraphService,
    document_service: DocumentService,
) -> SyncedItemInfo:
    """
    Sync a single file from SharePoint/OneDrive.

    Args:
        db: Database session
        connection: Provider connection
        folder: Target RADEX folder
        item: SharePoint item to sync
        current_user: Current user
        graph_service: Microsoft Graph service instance
        document_service: Document service instance

    Returns:
        SyncedItemInfo with result

    Raises:
        Exception: If sync fails (caught by caller)
    """
    # Check if item is already synced (idempotency)
    existing_ref = (
        db.query(ProviderItemRef)
        .filter(
            ProviderItemRef.provider == ProviderType.sharepoint,
            ProviderItemRef.drive_id == item.drive_id,
            ProviderItemRef.item_id == item.item_id,
        )
        .first()
    )

    if existing_ref:
        # Already synced - return existing document info
        document = db.query(Document).filter(Document.id == existing_ref.document_id).first()
        return SyncedItemInfo(
            sharepoint_item_id=item.item_id,
            document_id=existing_ref.document_id,
            filename=document.filename if document else "Unknown",
            status="skipped",
            message="File already synced",
        )

    # Get item metadata from SharePoint
    metadata = await graph_service.get_item_metadata(
        connection, item.drive_id, item.item_id
    )

    filename = metadata.get("name", "unnamed_file")

    # Check if it's a folder (we only sync files)
    if "folder" in metadata:
        return SyncedItemInfo(
            sharepoint_item_id=item.item_id,
            document_id=UUID("00000000-0000-0000-0000-000000000000"),
            filename=filename,
            status="skipped",
            message="Folders are not supported for sync (files only)",
        )

    # Download file content to temporary file
    file_content = await graph_service.download_file(
        connection, item.drive_id, item.item_id
    )

    # Use context manager for automatic cleanup
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save to temp file
        temp_file_path = os.path.join(temp_dir, filename)
        with open(temp_file_path, "wb") as f:
            f.write(file_content)

        # Upload to MinIO and create document record using existing service
        # This reuses the existing upload functionality
        document = await document_service.create_document_from_file(
            folder_id=folder.id,
            file_path=temp_file_path,
            filename=filename,
            file_size=len(file_content),
            uploaded_by=current_user.id,
        )

    # Create provider reference for idempotency
    provider_ref = ProviderItemRef(
        provider=ProviderType.sharepoint,
        connection_id=connection.id,
        document_id=document.id,
        drive_id=item.drive_id,
        item_id=item.item_id,
        etag=item.e_tag,
        name=filename,
        size=len(file_content),
        last_modified=metadata.get("lastModifiedDateTime"),
        content_hash=metadata.get("file", {}).get("hashes", {}).get("quickXorHash"),
    )
    db.add(provider_ref)
    db.commit()

    return SyncedItemInfo(
        sharepoint_item_id=item.item_id,
        document_id=document.id,
        filename=filename,
        status="success",
        message="File synced successfully",
    )
