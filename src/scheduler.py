"""
Scheduler module for automated data extraction and updates
"""

import schedule
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import *
from data_extractor import EarningsExtractor
from rag_system import RAGSystem
from utils import setup_logging, create_backup

logger = logging.getLogger(__name__)

class DataScheduler:
    """Handles scheduled data extraction and maintenance tasks"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.scheduler = BackgroundScheduler()
        self.extractor = None
        self.rag_system = None
        self.is_running = False
        self.jobs = {}
        
        # Initialize components
        self._initialize_components()
        
        # Setup default jobs if enabled
        if SCHEDULER_ENABLED:
            self._setup_default_jobs()
    
    def _initialize_components(self):
        """Initialize extractor and RAG system"""
        try:
            self.extractor = EarningsExtractor()
            self.rag_system = RAGSystem()
            logger.info("Scheduler components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize scheduler components: {str(e)}")
    
    def _setup_default_jobs(self):
        """Setup default scheduled jobs"""
        try:
            # Daily data extraction job
            self.add_daily_extraction_job(
                time=DAILY_UPDATE_TIME,
                companies=list(COMPANIES.keys())[:5],  # Limit to first 5 companies for daily runs
                job_id="daily_extraction"
            )
            
            # Weekly full sync job
            self.add_weekly_full_sync_job(
                day=WEEKLY_FULL_SYNC,
                job_id="weekly_full_sync"
            )
            
            # Daily backup job
            self.add_backup_job(
                time="02:00",  # 2 AM
                job_id="daily_backup"
            )
            
            # Health check job
            self.add_health_check_job(
                interval_hours=6,
                job_id="health_check"
            )
            
            logger.info("Default scheduled jobs setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup default jobs: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                logger.info("Scheduler started successfully")
            else:
                logger.warning("Scheduler is already running")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Scheduler stopped successfully")
            else:
                logger.warning("Scheduler is not running")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}")
    
    def add_daily_extraction_job(self, time: str, companies: List[str], job_id: str = None):
        """Add daily data extraction job"""
        try:
            hour, minute = map(int, time.split(':'))
            
            job = self.scheduler.add_job(
                func=self._daily_extraction_task,
                trigger=CronTrigger(hour=hour, minute=minute),
                args=[companies],
                id=job_id or f"daily_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                replace_existing=True,
                max_instances=1
            )
            
            self.jobs[job.id] = {
                'type': 'daily_extraction',
                'companies': companies,
                'time': time,
                'created': datetime.now().isoformat()
            }
            
            logger.info(f"Daily extraction job added: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to add daily extraction job: {str(e)}")
            return None
    
    def add_weekly_full_sync_job(self, day: str, job_id: str = None):
        """Add weekly full synchronization job"""
        try:
            # Convert day name to number (0=Monday, 6=Sunday)
            day_mapping = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            day_num = day_mapping.get(day.lower(), 6)  # Default to Sunday
            
            job = self.scheduler.add_job(
                func=self._weekly_full_sync_task,
                trigger=CronTrigger(day_of_week=day_num, hour=1, minute=0),  # 1 AM
                id=job_id or f"weekly_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                replace_existing=True,
                max_instances=1
            )
            
            self.jobs[job.id] = {
                'type': 'weekly_full_sync',
                'day': day,
                'created': datetime.now().isoformat()
            }
            
            logger.info(f"Weekly full sync job added: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to add weekly full sync job: {str(e)}")
            return None
    
    def add_backup_job(self, time: str, job_id: str = None):
        """Add daily backup job"""
        try:
            hour, minute = map(int, time.split(':'))
            
            job = self.scheduler.add_job(
                func=self._backup_task,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=job_id or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                replace_existing=True,
                max_instances=1
            )
            
            self.jobs[job.id] = {
                'type': 'backup',
                'time': time,
                'created': datetime.now().isoformat()
            }
            
            logger.info(f"Backup job added: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to add backup job: {str(e)}")
            return None
    
    def add_health_check_job(self, interval_hours: int, job_id: str = None):
        """Add periodic health check job"""
        try:
            job = self.scheduler.add_job(
                func=self._health_check_task,
                trigger='interval',
                hours=interval_hours,
                id=job_id or f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                replace_existing=True,
                max_instances=1
            )
            
            self.jobs[job.id] = {
                'type': 'health_check',
                'interval_hours': interval_hours,
                'created': datetime.now().isoformat()
            }
            
            logger.info(f"Health check job added: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to add health check job: {str(e)}")
            return None
    
    def add_custom_job(self, func: Callable, trigger_type: str, job_id: str = None, **trigger_args):
        """Add custom job with specified trigger"""
        try:
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger_type,
                id=job_id or f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                replace_existing=True,
                max_instances=1,
                **trigger_args
            )
            
            self.jobs[job.id] = {
                'type': 'custom',
                'function': func.__name__,
                'trigger': trigger_type,
                'created': datetime.now().isoformat()
            }
            
            logger.info(f"Custom job added: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to add custom job: {str(e)}")
            return None
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Job removed: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {str(e)}")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'func': job.func.__name__,
                    'trigger': str(job.trigger),
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'misfire_grace_time': job.misfire_grace_time,
                    'max_instances': job.max_instances
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {str(e)}")
            return None
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        try:
            jobs_list = []
            for job in self.scheduler.get_jobs():
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'func': job.func.__name__,
                    'trigger': str(job.trigger),
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'metadata': self.jobs.get(job.id, {})
                }
                jobs_list.append(job_info)
            
            return jobs_list
        except Exception as e:
            logger.error(f"Failed to list jobs: {str(e)}")
            return []
    
    def _daily_extraction_task(self, companies: List[str]):
        """Daily extraction task"""
        try:
            logger.info("Starting daily extraction task")
            
            if not self.extractor or not self.rag_system:
                logger.error("Components not initialized for daily extraction")
                return
            
            # Get current quarter and year
            now = datetime.now()
            current_year = str(now.year)
            current_quarter = f"Q{(now.month - 1) // 3 + 1}"
            
            # Extract data for selected companies
            results = self.extractor.batch_extract(
                companies=companies,
                years=[current_year],
                quarters=[current_quarter]
            )
            
            # Add to RAG system
            for detail in results['details']:
                if detail['status'] == 'success':
                    # Load extracted data and add to RAG
                    # This is a simplified implementation
                    pass
            
            logger.info(f"Daily extraction completed: {results['successful']} successful, {results['failed']} failed")
            
        except Exception as e:
            logger.error(f"Daily extraction task failed: {str(e)}")
    
    def _weekly_full_sync_task(self):
        """Weekly full synchronization task"""
        try:
            logger.info("Starting weekly full sync task")
            
            if not self.extractor or not self.rag_system:
                logger.error("Components not initialized for weekly sync")
                return
            
            # Extract data for all companies, current and previous quarter
            now = datetime.now()
            current_year = str(now.year)
            current_quarter = f"Q{(now.month - 1) // 3 + 1}"
            
            # Include previous quarter
            prev_quarter_num = ((now.month - 1) // 3 + 1) - 1
            if prev_quarter_num < 1:
                prev_quarter_num = 4
                prev_year = str(now.year - 1)
            else:
                prev_year = current_year
            prev_quarter = f"Q{prev_quarter_num}"
            
            quarters = [prev_quarter, current_quarter]
            years = [prev_year, current_year] if prev_year != current_year else [current_year]
            
            results = self.extractor.batch_extract(
                companies=list(COMPANIES.keys()),
                years=list(set(years)),
                quarters=quarters
            )
            
            logger.info(f"Weekly full sync completed: {results['successful']} successful, {results['failed']} failed")
            
        except Exception as e:
            logger.error(f"Weekly full sync task failed: {str(e)}")
    
    def _backup_task(self):
        """Backup task"""
        try:
            logger.info("Starting backup task")
            
            # Create backup of data directory
            backup_name = f"scheduled_backup_{datetime.now().strftime('%Y%m%d')}"
            success = create_backup(DATA_DIR, backup_name)
            
            if success:
                logger.info("Backup task completed successfully")
            else:
                logger.error("Backup task failed")
                
        except Exception as e:
            logger.error(f"Backup task failed: {str(e)}")
    
    def _health_check_task(self):
        """Health check task"""
        try:
            logger.info("Starting health check task")
            
            # Check Ollama connection
            if self.rag_system:
                ollama_status = self.rag_system.check_ollama_connection()
                if not ollama_status:
                    logger.warning("Ollama connection failed during health check")
                else:
                    logger.info("Ollama connection healthy")
            
            # Check disk space
            import shutil
            total, used, free = shutil.disk_usage(DATA_DIR)
            free_gb = free // (1024**3)
            
            if free_gb < 1:  # Less than 1GB free
                logger.warning(f"Low disk space: {free_gb}GB remaining")
            
            # Check log file size
            if os.path.exists(LOG_FILE):
                log_size_mb = os.path.getsize(LOG_FILE) // (1024**2)
                if log_size_mb > 100:  # Log file larger than 100MB
                    logger.warning(f"Large log file: {log_size_mb}MB")
            
            logger.info("Health check completed")
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    def run_job_now(self, job_id: str) -> bool:
        """Execute a job immediately"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func(*job.args, **job.kwargs)
                logger.info(f"Job {job_id} executed immediately")
                return True
            else:
                logger.error(f"Job {job_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to run job {job_id} immediately: {str(e)}")
            return False
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get overall scheduler status"""
        return {
            'is_running': self.is_running,
            'total_jobs': len(self.jobs),
            'active_jobs': len(self.scheduler.get_jobs()),
            'state': self.scheduler.state,
            'timezone': str(self.scheduler.timezone) if hasattr(self.scheduler, 'timezone') else None,
            'jobs': self.list_jobs()
        }
