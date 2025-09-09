from celery import Celery, Task
from celery.utils.log import get_task_logger
from typing import Dict, Any
from uuid import UUID
import os

from app.database import SessionLocal
from app.services.confluence import ConfluenceImportService
from app.models import ConfluenceImport, SyncStatus

logger = get_task_logger(__name__)

# Create Celery app
celery_app = Celery(
    'radex_workers',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
)


class CallbackTask(Task):
    """Base task with automatic database session handling"""
    
    def __call__(self, *args, **kwargs):
        with SessionLocal() as db:
            self.db = db
            try:
                return self.run(*args, **kwargs)
            finally:
                db.close()


@celery_app.task(bind=True, base=CallbackTask, name='confluence.import')
def process_confluence_import_task(
    self,
    import_id: str,
    include_attachments: bool = True,
    include_comments: bool = False
) -> Dict[str, Any]:
    """
    Celery task to process a Confluence import job
    
    Args:
        import_id: UUID of the import job
        include_attachments: Whether to import attachments
        include_comments: Whether to import comments
    
    Returns:
        Dict with import results
    """
    logger.info(f"Starting Confluence import job: {import_id}")
    
    try:
        # Convert string UUID to UUID object
        import_uuid = UUID(import_id)
        
        # Create import service with database session
        import_service = ConfluenceImportService(self.db)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Initializing import...'}
        )
        
        # Process the import
        import_job = import_service.process_import(
            import_id=import_uuid,
            include_attachments=include_attachments,
            include_comments=include_comments
        )
        
        # Prepare result
        result = {
            'import_id': str(import_job.id),
            'status': import_job.sync_status.value,
            'total_pages': import_job.total_pages,
            'processed_pages': import_job.processed_pages,
            'success': import_job.sync_status in [SyncStatus.COMPLETED, SyncStatus.PARTIAL]
        }
        
        if import_job.error_message:
            result['error'] = import_job.error_message
        
        logger.info(f"Completed Confluence import job: {import_id} - Status: {import_job.sync_status.value}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to process Confluence import {import_id}: {str(e)}")
        
        # Update import job status to failed
        try:
            import_job = self.db.query(ConfluenceImport).filter(
                ConfluenceImport.id == UUID(import_id)
            ).first()
            
            if import_job:
                import_job.sync_status = SyncStatus.FAILED
                import_job.error_message = str(e)
                self.db.commit()
        except:
            pass
        
        raise


@celery_app.task(bind=True, name='confluence.import.batch')
def process_batch_import_task(
    self,
    import_ids: list,
    include_attachments: bool = True
) -> Dict[str, Any]:
    """
    Process multiple Confluence imports in sequence
    
    Args:
        import_ids: List of import job UUIDs
        include_attachments: Whether to import attachments
    
    Returns:
        Dict with batch import results
    """
    results = []
    
    for import_id in import_ids:
        try:
            result = process_confluence_import_task.apply_async(
                args=[import_id, include_attachments, False]
            ).get()
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process import {import_id}: {str(e)}")
            results.append({
                'import_id': import_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'total': len(import_ids),
        'successful': sum(1 for r in results if r.get('success', False)),
        'failed': sum(1 for r in results if not r.get('success', False)),
        'results': results
    }


@celery_app.task(bind=True, base=CallbackTask, name='confluence.import.status')
def get_import_status_task(self, import_id: str) -> Dict[str, Any]:
    """
    Get the current status of an import job
    
    Args:
        import_id: UUID of the import job
    
    Returns:
        Dict with import status
    """
    try:
        import_job = self.db.query(ConfluenceImport).filter(
            ConfluenceImport.id == UUID(import_id)
        ).first()
        
        if not import_job:
            return {'error': 'Import job not found'}
        
        progress = 0
        if import_job.total_pages > 0:
            progress = (import_job.processed_pages / import_job.total_pages) * 100
        
        return {
            'import_id': str(import_job.id),
            'status': import_job.sync_status.value,
            'total_pages': import_job.total_pages,
            'processed_pages': import_job.processed_pages,
            'progress_percentage': progress,
            'error_message': import_job.error_message,
            'created_at': import_job.created_at.isoformat() if import_job.created_at else None,
            'last_sync_at': import_job.last_sync_at.isoformat() if import_job.last_sync_at else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get import status for {import_id}: {str(e)}")
        return {'error': str(e)}