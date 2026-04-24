"""
Professional Training Scheduler
Runs automatic training at optimal times
"""

import schedule
import time
import logging
import threading
from datetime import datetime
import traceback

from .trainer import ProfessionalTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingScheduler:
    def __init__(self, trainer: ProfessionalTrainer):
        self.trainer = trainer
        self.is_running = False
        self.thread = None
        
    def daily_training_job(self):
        """Main training job - runs daily at 3 AM"""
        logger.info("⏰ Starting daily training job")
        start_time = time.time()
        
        try:
            # Train all cities
            results = self.trainer.train_all_cities()
            
            # Log summary
            successful = sum(1 for r in results.values() 
                           if r.get('status') != 'failed')
            failed = len(results) - successful
            
            duration = time.time() - start_time
            
            logger.info(f"📊 Training Summary:")
            logger.info(f"   • Total cities: {len(results)}")
            logger.info(f"   • Successful: {successful}")
            logger.info(f"   • Failed: {failed}")
            logger.info(f"   • Duration: {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Training job failed: {e}")
            traceback.print_exc()
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule daily training at 3 AM
        schedule.every().day.at("03:00").do(self.daily_training_job)
        
        # For testing: run every hour (remove this in production)
        # schedule.every(1).hours.do(self.daily_training_job)
        
        self.is_running = True
        logger.info("✅ Scheduler started - Daily training at 3 AM")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def start_in_background(self):
        """Start scheduler in background thread"""
        self.thread = threading.Thread(target=self.start_scheduler, daemon=True)
        self.thread.start()
        logger.info("✅ Background scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("⏹️ Scheduler stopped")