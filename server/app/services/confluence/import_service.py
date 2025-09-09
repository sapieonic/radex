import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models import (
    ConfluenceImport, ImportType, SyncStatus, 
    ConfluencePage, ConfluenceCredential,
    Folder, Document, User
)
from app.services.confluence.client import ConfluenceClient
from app.services.confluence.extractor import ConfluenceExtractor
from app.services.confluence.auth_service import ConfluenceAuthService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.permission_service import PermissionService
from app.core.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)


class ConfluenceImportService:
    """Service for importing content from Confluence"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = ConfluenceAuthService(db)
        self.extractor = ConfluenceExtractor()
        self.document_service = DocumentService(db)
        self.embedding_service = EmbeddingService(db)
        self.permission_service = PermissionService(db)
    
    def create_import_job(
        self,
        user: User,
        credential_id: uuid.UUID,
        folder_id: uuid.UUID,
        import_type: ImportType,
        space_key: Optional[str] = None,
        page_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ConfluenceImport:
        """Create a new import job"""
        
        # Verify credential belongs to user
        credential = self.auth_service.get_credential(credential_id, user.id)
        
        # Verify folder exists and user has write permission
        folder = self.db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise NotFoundException("Target folder not found")
        
        if not self.permission_service.check_folder_permission(user.id, folder.id, "write"):
            raise BadRequestException("You don't have write permission for this folder")
        
        # Validate import parameters
        if import_type == ImportType.SPACE and not space_key:
            raise BadRequestException("Space key is required for space import")
        elif import_type in [ImportType.PAGE, ImportType.PAGE_TREE] and not page_id:
            raise BadRequestException("Page ID is required for page import")
        
        # Create import job
        import_job = ConfluenceImport(
            credential_id=credential_id,
            folder_id=folder_id,
            space_key=space_key,
            page_id=page_id,
            import_type=import_type,
            sync_status=SyncStatus.PENDING,
            import_metadata=metadata or {}
        )
        
        self.db.add(import_job)
        self.db.commit()
        self.db.refresh(import_job)
        
        return import_job
    
    def process_import(
        self, 
        import_id: uuid.UUID,
        include_attachments: bool = True,
        include_comments: bool = False
    ) -> ConfluenceImport:
        """Process an import job"""
        
        # Get import job
        import_job = self.db.query(ConfluenceImport).filter(
            ConfluenceImport.id == import_id
        ).first()
        
        if not import_job:
            raise NotFoundException("Import job not found")
        
        # Update status
        import_job.sync_status = SyncStatus.IN_PROGRESS
        self.db.commit()
        
        try:
            # Create Confluence client
            client = ConfluenceClient(import_job.credential, self.auth_service)
            
            # Test connection
            if not client.test_connection():
                raise BadRequestException("Failed to connect to Confluence")
            
            # Get pages based on import type
            pages = self._fetch_pages(client, import_job)
            
            # Update total count
            import_job.total_pages = len(pages)
            self.db.commit()
            
            # Process each page
            created_documents = []
            for page_data in pages:
                try:
                    doc = self._process_page(
                        import_job, 
                        page_data, 
                        client,
                        include_attachments
                    )
                    if doc:
                        created_documents.append(doc)
                    
                    import_job.processed_pages += 1
                    self.db.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to process page {page_data.get('id')}: {str(e)}")
                    continue
            
            # Update job status
            if import_job.processed_pages == import_job.total_pages:
                import_job.sync_status = SyncStatus.COMPLETED
            else:
                import_job.sync_status = SyncStatus.PARTIAL
            
            import_job.last_sync_at = datetime.utcnow()
            self.db.commit()
            
            # Process embeddings for all documents
            for doc in created_documents:
                try:
                    self.embedding_service.process_document(doc.id)
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for document {doc.id}: {str(e)}")
            
            return import_job
            
        except Exception as e:
            import_job.sync_status = SyncStatus.FAILED
            import_job.error_message = str(e)
            self.db.commit()
            raise
    
    def _fetch_pages(
        self, 
        client: ConfluenceClient, 
        import_job: ConfluenceImport
    ) -> List[Dict[str, Any]]:
        """Fetch pages based on import type"""
        
        if import_job.import_type == ImportType.SPACE:
            return client.get_space_content(import_job.space_key)
        elif import_job.import_type == ImportType.PAGE:
            return [client.get_page_by_id(import_job.page_id)]
        elif import_job.import_type == ImportType.PAGE_TREE:
            return client.get_page_tree(import_job.page_id)
        else:
            raise BadRequestException(f"Unknown import type: {import_job.import_type}")
    
    def _process_page(
        self,
        import_job: ConfluenceImport,
        page_data: Dict[str, Any],
        client: ConfluenceClient,
        include_attachments: bool = True
    ) -> Optional[Document]:
        """Process a single Confluence page"""
        
        # Extract content and metadata
        extracted = self.extractor.extract_page_content(page_data)
        
        # Check if page already exists
        existing_page = self.db.query(ConfluencePage).filter(
            ConfluencePage.import_id == import_job.id,
            ConfluencePage.confluence_page_id == page_data['id']
        ).first()
        
        if existing_page:
            # Check if content has changed
            if existing_page.content_hash == extracted['content_hash']:
                logger.info(f"Page {page_data['id']} unchanged, skipping")
                return None
            
            # Update existing page
            document = self._update_document(existing_page, extracted)
        else:
            # Create new page and document
            document = self._create_document(import_job, page_data, extracted)
        
        # Process attachments if requested
        if include_attachments and extracted['has_attachments']:
            self._process_attachments(import_job, page_data['id'], document, client)
        
        return document
    
    def _create_document(
        self,
        import_job: ConfluenceImport,
        page_data: Dict[str, Any],
        extracted: Dict[str, Any]
    ) -> Document:
        """Create a new document from a Confluence page"""
        
        # Determine folder path
        folder = import_job.folder
        page_title = extracted['metadata']['title']
        
        # Create subfolder for space if importing entire space
        if import_job.import_type == ImportType.SPACE:
            space_folder = self._ensure_folder(
                parent=folder,
                name=extracted['metadata']['space_name'] or import_job.space_key,
                owner_id=folder.owner_id
            )
            target_folder = space_folder
        else:
            target_folder = folder
        
        # Save content to file
        file_name = f"{page_title}.md"
        file_content = extracted['content'].encode('utf-8')
        
        # Create document
        document = Document(
            folder_id=target_folder.id,
            name=file_name,
            mime_type='text/markdown',
            size=len(file_content),
            storage_path='',  # Will be set by document service
            metadata={
                'source': 'confluence',
                'confluence_metadata': extracted['metadata']
            }
        )
        
        self.db.add(document)
        self.db.flush()
        
        # Store file content
        storage_path = self.document_service.store_file(
            file_content=file_content,
            file_name=file_name,
            document_id=str(document.id)
        )
        document.storage_path = storage_path
        
        # Create ConfluencePage record
        confluence_page = ConfluencePage(
            import_id=import_job.id,
            document_id=document.id,
            confluence_page_id=page_data['id'],
            confluence_space_key=extracted['metadata']['space_key'],
            title=page_title,
            parent_page_id=extracted['metadata']['parent_id'],
            version_number=str(extracted['metadata']['version']),
            author_email=extracted['metadata']['created_by'],
            created_date=extracted['metadata']['created_date'],
            modified_date=extracted['metadata']['modified_date'],
            has_attachments=extracted['has_attachments'],
            content_hash=extracted['content_hash'],
            page_metadata=extracted['metadata']
        )
        
        self.db.add(confluence_page)
        self.db.commit()
        
        return document
    
    def _update_document(
        self,
        existing_page: ConfluencePage,
        extracted: Dict[str, Any]
    ) -> Document:
        """Update an existing document with new content"""
        
        document = existing_page.document
        if not document:
            logger.warning(f"Document not found for page {existing_page.id}")
            return None
        
        # Update content
        file_content = extracted['content'].encode('utf-8')
        storage_path = self.document_service.store_file(
            file_content=file_content,
            file_name=document.name,
            document_id=str(document.id)
        )
        
        # Update document
        document.size = len(file_content)
        document.storage_path = storage_path
        document.metadata['confluence_metadata'] = extracted['metadata']
        
        # Update ConfluencePage
        existing_page.version_number = str(extracted['metadata']['version'])
        existing_page.modified_date = extracted['metadata']['modified_date']
        existing_page.content_hash = extracted['content_hash']
        existing_page.page_metadata = extracted['metadata']
        
        self.db.commit()
        
        # Re-generate embeddings
        self.embedding_service.process_document(document.id)
        
        return document
    
    def _process_attachments(
        self,
        import_job: ConfluenceImport,
        page_id: str,
        parent_document: Document,
        client: ConfluenceClient
    ):
        """Process attachments for a page"""
        
        try:
            attachments = client.get_attachments(page_id)
            
            for attachment_data in attachments:
                try:
                    attachment_info = self.extractor.extract_attachment_info(attachment_data)
                    
                    # Download attachment
                    if attachment_info['download_url']:
                        content = client.download_attachment(attachment_info['download_url'])
                        
                        # Create document for attachment
                        attachment_doc = Document(
                            folder_id=parent_document.folder_id,
                            name=attachment_info['filename'],
                            mime_type=attachment_info['media_type'],
                            size=len(content),
                            storage_path='',
                            metadata={
                                'source': 'confluence_attachment',
                                'parent_page_id': page_id,
                                'attachment_info': attachment_info
                            }
                        )
                        
                        self.db.add(attachment_doc)
                        self.db.flush()
                        
                        # Store attachment
                        storage_path = self.document_service.store_file(
                            file_content=content,
                            file_name=attachment_info['filename'],
                            document_id=str(attachment_doc.id)
                        )
                        attachment_doc.storage_path = storage_path
                        
                        self.db.commit()
                        
                except Exception as e:
                    logger.error(f"Failed to process attachment {attachment_data.get('id')}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to fetch attachments for page {page_id}: {str(e)}")
    
    def _ensure_folder(self, parent: Folder, name: str, owner_id: uuid.UUID) -> Folder:
        """Ensure a folder exists, creating it if necessary"""
        
        # Check if folder already exists
        existing = self.db.query(Folder).filter(
            Folder.parent_id == parent.id,
            Folder.name == name
        ).first()
        
        if existing:
            return existing
        
        # Create new folder
        new_folder = Folder(
            name=name,
            parent_id=parent.id,
            owner_id=owner_id,
            path=f"{parent.path}/{name}" if parent.path != "/" else f"/{name}"
        )
        
        self.db.add(new_folder)
        self.db.commit()
        self.db.refresh(new_folder)
        
        return new_folder
    
    def get_import_status(self, import_id: uuid.UUID) -> Dict[str, Any]:
        """Get status of an import job"""
        
        import_job = self.db.query(ConfluenceImport).filter(
            ConfluenceImport.id == import_id
        ).first()
        
        if not import_job:
            raise NotFoundException("Import job not found")
        
        return {
            'id': import_job.id,
            'status': import_job.sync_status,
            'total_pages': import_job.total_pages,
            'processed_pages': import_job.processed_pages,
            'error_message': import_job.error_message,
            'created_at': import_job.created_at,
            'last_sync_at': import_job.last_sync_at
        }