from celery import Celery
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID
import os

from app.database import SessionLocal
from app.services.confluence import ConfluenceImportService, ConfluenceClient, ConfluenceAuthService
from app.models import ConfluenceImport, ConfluencePage, SyncStatus
from app.services.confluence.extractor import ConfluenceExtractor

logger = get_task_logger(__name__)

# Create Celery app
celery_app = Celery(
    'radex_sync_workers',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure Celery beat schedule for periodic syncs
celery_app.conf.beat_schedule = {
    'sync-confluence-content': {
        'task': 'confluence.sync.scheduled',
        'schedule': timedelta(hours=int(os.getenv('CONFLUENCE_SYNC_INTERVAL_HOURS', '24'))),
    },
}


@celery_app.task(name='confluence.sync')
def sync_confluence_content_task(import_id: str, force_full_sync: bool = False) -> Dict[str, Any]:
    """
    Sync an existing Confluence import with latest content
    
    Args:
        import_id: UUID of the import job to sync
        force_full_sync: Whether to force a full sync regardless of timestamps
    
    Returns:
        Dict with sync results
    """
    logger.info(f"Starting Confluence sync for import: {import_id}")
    
    with SessionLocal() as db:
        try:
            # Get import job
            import_job = db.query(ConfluenceImport).filter(
                ConfluenceImport.id == UUID(import_id)
            ).first()
            
            if not import_job:
                return {'error': 'Import job not found'}
            
            # Update status
            import_job.sync_status = SyncStatus.IN_PROGRESS
            db.commit()
            
            # Initialize services
            auth_service = ConfluenceAuthService(db)
            client = ConfluenceClient(import_job.credential, auth_service)
            extractor = ConfluenceExtractor()
            import_service = ConfluenceImportService(db)
            
            # Track sync metrics
            pages_updated = 0
            pages_added = 0
            pages_deleted = 0
            
            # Get current pages from Confluence
            if import_job.import_type.value == 'space':
                current_pages = client.get_space_content(import_job.space_key)
            elif import_job.import_type.value == 'page_tree':
                current_pages = client.get_page_tree(import_job.page_id)
            else:
                current_pages = [client.get_page_by_id(import_job.page_id)]
            
            # Get existing pages from database
            existing_pages = db.query(ConfluencePage).filter(
                ConfluencePage.import_id == import_job.id
            ).all()
            
            existing_page_ids = {p.confluence_page_id for p in existing_pages}
            current_page_ids = {p['id'] for p in current_pages}
            
            # Find pages to delete (no longer in Confluence)
            pages_to_delete = existing_page_ids - current_page_ids
            for page_id in pages_to_delete:
                page = next(p for p in existing_pages if p.confluence_page_id == page_id)
                if page.document:
                    db.delete(page.document)
                db.delete(page)
                pages_deleted += 1
            
            # Process current pages
            for page_data in current_pages:
                page_id = page_data['id']
                
                # Extract content
                extracted = extractor.extract_page_content(page_data)
                
                # Check if page exists
                existing_page = next((p for p in existing_pages if p.confluence_page_id == page_id), None)
                
                if existing_page:
                    # Check if content has changed
                    if force_full_sync or existing_page.content_hash != extracted['content_hash']:
                        # Update existing page
                        import_service._update_document(existing_page, extracted)
                        pages_updated += 1
                    else:
                        logger.debug(f"Page {page_id} unchanged, skipping")
                else:
                    # Create new page
                    import_service._create_document(import_job, page_data, extracted)
                    pages_added += 1
            
            # Update import job
            import_job.sync_status = SyncStatus.COMPLETED
            import_job.last_sync_at = datetime.utcnow()
            import_job.processed_pages = len(current_pages)
            import_job.total_pages = len(current_pages)
            db.commit()
            
            result = {
                'import_id': str(import_job.id),
                'status': 'completed',
                'pages_updated': pages_updated,
                'pages_added': pages_added,
                'pages_deleted': pages_deleted,
                'total_pages': len(current_pages)
            }
            
            logger.info(f"Completed Confluence sync for import {import_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to sync Confluence content for import {import_id}: {str(e)}")
            
            # Update import job status
            if import_job:
                import_job.sync_status = SyncStatus.FAILED
                import_job.error_message = str(e)
                db.commit()
            
            return {'error': str(e)}


@celery_app.task(name='confluence.sync.scheduled')
def scheduled_confluence_sync() -> Dict[str, Any]:
    """
    Scheduled task to sync all active Confluence imports
    
    Returns:
        Dict with sync results for all imports
    """
    logger.info("Starting scheduled Confluence sync")
    
    with SessionLocal() as db:
        # Get all imports that need syncing
        sync_interval_hours = int(os.getenv('CONFLUENCE_SYNC_INTERVAL_HOURS', '24'))
        cutoff_time = datetime.utcnow() - timedelta(hours=sync_interval_hours)
        
        imports_to_sync = db.query(ConfluenceImport).filter(
            (ConfluenceImport.last_sync_at < cutoff_time) | 
            (ConfluenceImport.last_sync_at == None),
            ConfluenceImport.sync_status != SyncStatus.FAILED
        ).all()
        
        results = []
        for import_job in imports_to_sync:
            try:
                result = sync_confluence_content_task.apply_async(
                    args=[str(import_job.id), False]
                ).get()
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to sync import {import_job.id}: {str(e)}")
                results.append({
                    'import_id': str(import_job.id),
                    'error': str(e)
                })
        
        return {
            'total_synced': len(results),
            'successful': sum(1 for r in results if 'error' not in r),
            'failed': sum(1 for r in results if 'error' in r),
            'results': results
        }


@celery_app.task(name='confluence.sync.check_changes')
def check_confluence_changes(import_id: str) -> Dict[str, Any]:
    """
    Check if there are any changes in Confluence content without syncing
    
    Args:
        import_id: UUID of the import job to check
    
    Returns:
        Dict with change detection results
    """
    with SessionLocal() as db:
        try:
            # Get import job
            import_job = db.query(ConfluenceImport).filter(
                ConfluenceImport.id == UUID(import_id)
            ).first()
            
            if not import_job:
                return {'error': 'Import job not found'}
            
            # Initialize services
            auth_service = ConfluenceAuthService(db)
            client = ConfluenceClient(import_job.credential, auth_service)
            extractor = ConfluenceExtractor()
            
            # Get current pages from Confluence
            if import_job.import_type.value == 'space':
                current_pages = client.get_space_content(import_job.space_key)
            elif import_job.import_type.value == 'page_tree':
                current_pages = client.get_page_tree(import_job.page_id)
            else:
                current_pages = [client.get_page_by_id(import_job.page_id)]
            
            # Get existing pages from database
            existing_pages = db.query(ConfluencePage).filter(
                ConfluencePage.import_id == import_job.id
            ).all()
            
            existing_page_map = {p.confluence_page_id: p for p in existing_pages}
            
            # Check for changes
            changes = {
                'pages_to_add': [],
                'pages_to_update': [],
                'pages_to_delete': []
            }
            
            current_page_ids = set()
            for page_data in current_pages:
                page_id = page_data['id']
                current_page_ids.add(page_id)
                
                if page_id in existing_page_map:
                    # Check if content has changed
                    extracted = extractor.extract_page_content(page_data)
                    if existing_page_map[page_id].content_hash != extracted['content_hash']:
                        changes['pages_to_update'].append({
                            'id': page_id,
                            'title': page_data['title']
                        })
                else:
                    changes['pages_to_add'].append({
                        'id': page_id,
                        'title': page_data['title']
                    })
            
            # Check for deleted pages
            for page_id in existing_page_map:
                if page_id not in current_page_ids:
                    changes['pages_to_delete'].append({
                        'id': page_id,
                        'title': existing_page_map[page_id].title
                    })
            
            return {
                'import_id': str(import_job.id),
                'has_changes': bool(changes['pages_to_add'] or changes['pages_to_update'] or changes['pages_to_delete']),
                'changes': changes,
                'summary': {
                    'to_add': len(changes['pages_to_add']),
                    'to_update': len(changes['pages_to_update']),
                    'to_delete': len(changes['pages_to_delete'])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to check changes for import {import_id}: {str(e)}")
            return {'error': str(e)}