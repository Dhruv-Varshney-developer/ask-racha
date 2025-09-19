import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentUpdateScheduler:
    """Scheduler for automatic document updates and session cleanup"""
    
    def __init__(self, rag_instance=None, context_manager=None, test_mode=False):
        self.rag = rag_instance
        self.context_manager = context_manager
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.is_running = False
        self.test_mode = test_mode
        # In test mode: 1 minute interval, 2 minutes expiry
        self.cleanup_interval = 1 if test_mode else 15  # minutes
        self.session_expiry = 120 if test_mode else 10800  # 2 mins or 3 hours in seconds
        
    def set_rag_instance(self, rag_instance):
        """Set the RAG instance for document updates"""
        self.rag = rag_instance
        logger.info("RAG instance set for document scheduler")
        
    def set_context_manager(self, context_manager):
        """Set the context manager for session cleanup"""
        self.context_manager = context_manager
        logger.info("Context manager set for session cleanup")
        
    def cleanup_old_sessions(self):
        """Remove sessions older than 3 hours"""
        if not self.context_manager:
            logger.warning("No context manager set for cleanup")
            return
            
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.context_manager.sessions.items():
            created_time = datetime.fromisoformat(session.created_at)
            age = (current_time - created_time).total_seconds()
            
            if age > self.session_expiry:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.context_manager.sessions[session_id]
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} sessions older than 3 hours")
    
    def start(self):
        """Start the scheduler with both document updates and session cleanup"""
        if not self.is_running:
            try:
                # Schedule monthly document update (1st of month at 2:00 AM)
                self.scheduler.add_job(
                    func=self._update_documents_monthly,
                    trigger=CronTrigger(day=1, hour=2, minute=0),
                    id='monthly_document_update',
                    name='Monthly Document Update',
                    replace_existing=True
                )
                
                # Schedule weekly health check (every Sunday at 3:00 AM)
                self.scheduler.add_job(
                    func=self._health_check_job,
                    trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
                    id='weekly_health_check',
                    name='Weekly Health Check',
                    replace_existing=True
                )
                
                # Schedule session cleanup every 15 minutes
                self.scheduler.add_job(
                    self.cleanup_old_sessions,
                    'interval',
                    minutes=self.cleanup_interval,
                    id='session_cleanup'
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info("Scheduler started with document updates and session cleanup")
                logger.info("Monthly updates scheduled for 1st of month at 2:00 AM")
                logger.info("Weekly health checks scheduled for Sundays at 3:00 AM")
                
            except Exception as e:
                logger.error(f"Failed to start scheduler: {e}")
                self.is_running = False
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Document update scheduler stopped")
            except Exception as e:
                logger.error(f"Failed to stop scheduler: {e}")
    
    def _update_documents_monthly(self):
        """Monthly job to update documents"""
        try:
            logger.info("Starting monthly document update...")
            
            if not self.rag:
                logger.warning("RAG instance not available, skipping monthly update")
                return
            
            # Default URLs for monthly updates
            default_urls = [
                "https://docs.storacha.network/quickstart/",
                "https://docs.storacha.network/concepts/ucans-and-storacha/",
            ]
            
            try:
                stats = self.rag.vector_store.get_stats()
                if stats["success"]:
                    current_count = stats["stats"].points_count
                    logger.info(f"Current documents in vector store: {current_count}")
            except Exception as e:
                logger.warning(f"Could not get current stats: {e}")
            
            # Load updated documents
            result = self.rag.load_documents(default_urls)
            
            if result['success']:
                logger.info(f" Monthly update completed successfully")
                logger.info(f"   Loaded: {result['document_count']} documents")
                logger.info(f"   Total characters: {result.get('total_chars', 'N/A')}")
                
                # Get updated stats
                try:
                    new_stats = self.rag.vector_store.get_stats()
                    if new_stats["success"]:
                        new_count = new_stats["stats"].points_count
                        logger.info(f"   New total documents: {new_count}")
                        if 'current_count' in locals():
                            change = new_count - current_count
                            if change > 0:
                                logger.info(f"   Documents added: +{change}")
                            elif change < 0:
                                logger.info(f"   Documents removed: {change}")
                            else:
                                logger.info(f"   No change in document count")
                except Exception as e:
                    logger.warning(f"Could not get updated stats: {e}")
                    
            else:
                logger.error(f"Monthly update failed: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error in monthly document update: {e}")
    
    def _health_check_job(self):
        """Weekly health check job"""
        try:
            logger.info("Running weekly health check...")
            
            if not self.rag:
                logger.warning("RAG instance not available for health check")
                return
            
            # Check vector store health
            try:
                stats = self.rag.vector_store.get_stats()
                if stats["success"]:
                    logger.info(f"Vector store healthy: {stats['stats'].points_count} documents")
                else:
                    logger.warning(f"Vector store issues: {stats['message']}")
            except Exception as e:
                logger.error(f"Vector store health check failed: {e}")
            
            # Check RAG system status
            try:
                rag_status = self.rag.get_status()
                logger.info(f"RAG system status: {rag_status['documents_loaded']} documents loaded")
            except Exception as e:
                logger.error(f"RAG status check failed: {e}")
                
        except Exception as e:
            logger.error(f"Error in weekly health check: {e}")
    
    def _job_listener(self, event):
        """Listener for job execution events"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
            logger.error(f"Traceback: {event.traceback}")
        else:
            logger.info(f"Job {event.job_id} executed successfully")
    
    def get_status(self):
        """Get scheduler status"""
        if not self.is_running:
            return {
                'status': 'stopped',
                'message': 'Scheduler is not running'
            }
        
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return {
                'status': 'running',
                'jobs': jobs,
                'job_count': len(jobs)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error getting scheduler status: {e}'
            }
    
    def trigger_manual_update(self):
        """Manually trigger document update (for testing/admin use)"""
        try:
            logger.info("Manual document update triggered...")
            self._update_documents_monthly()
            return {'success': True, 'message': 'Manual update completed'}
        except Exception as e:
            logger.error(f"Manual update failed: {e}")
            return {'success': False, 'message': f'Manual update failed: {e}'} 