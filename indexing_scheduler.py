import os
import sys
import time
import logging
import argparse
import schedule
from datetime import datetime
from typing import List, Optional

from google_indexing import IndexingManager
from url_manager import URLManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("indexing_scheduler")

class IndexingScheduler:
    """
    Scheduler for Google Indexing tasks
    """
    def __init__(self, api_keys_dir: str = "api_keys", urls_file: str = "urls.json"):
        """
        Initialize the indexing scheduler
        
        Args:
            api_keys_dir: Directory containing Google API service account JSON files
            urls_file: Path to the JSON file storing URL data
        """
        self.api_keys_dir = api_keys_dir
        self.urls_file = urls_file
        
        # Create directories if they don't exist
        os.makedirs(api_keys_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        self.indexing_manager = IndexingManager(api_keys_dir)
        self.url_manager = URLManager(urls_file)
        
    def run_indexing_task(self, batch_size: int = 10, retry_failed: bool = False):
        """
        Run a single indexing task
        
        Args:
            batch_size: Number of URLs to process in this batch
            retry_failed: Whether to retry failed URLs
        """
        logger.info(f"Starting indexing task at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Reset failed URLs if requested
        if retry_failed:
            reset_count = self.url_manager.reset_failed_urls()
            logger.info(f"Reset {reset_count} failed URLs to pending status")
            
        # Get pending URLs
        pending_urls = self.url_manager.get_pending_urls(limit=batch_size)
        
        if not pending_urls:
            logger.info("No pending URLs to index")
            return
            
        logger.info(f"Processing {len(pending_urls)} URLs")
        
        # Process each URL
        results = self.indexing_manager.index_urls(pending_urls)
        
        # Update URL statuses based on results
        for result in results:
            url = result["url"]
            success = "error" not in result["result"]
            self.url_manager.mark_as_indexed(url, success)
            
        logger.info(f"Completed indexing task at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def start_scheduler(self, interval_minutes: int = 60, batch_size: int = 10, retry_failed: bool = False):
        """
        Start the scheduler to run at regular intervals
        
        Args:
            interval_minutes: Minutes between runs
            batch_size: Number of URLs to process in each batch
            retry_failed: Whether to retry failed URLs
        """
        logger.info(f"Starting scheduler with {interval_minutes} minute interval")
        
        # Schedule the job
        schedule.every(interval_minutes).minutes.do(
            self.run_indexing_task, 
            batch_size=batch_size,
            retry_failed=retry_failed
        )
        
        # Run immediately once
        self.run_indexing_task(batch_size=batch_size, retry_failed=retry_failed)
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(1)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Google Indexing Scheduler")
    
    # Main command arguments
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of URLs to process in each batch")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed URLs")
    parser.add_argument("--interval", type=int, default=60, help="Minutes between scheduled runs")
    
    # Directory and file settings
    parser.add_argument("--api-keys-dir", type=str, default="api_keys", help="Directory containing API key files")
    parser.add_argument("--urls-file", type=str, default="urls.json", help="File containing URLs to index")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Initialize the scheduler
    scheduler = IndexingScheduler(
        api_keys_dir=args.api_keys_dir,
        urls_file=args.urls_file
    )
    
    # Run once or start the scheduler
    if args.run_once:
        scheduler.run_indexing_task(
            batch_size=args.batch_size,
            retry_failed=args.retry_failed
        )
    else:
        try:
            scheduler.start_scheduler(
                interval_minutes=args.interval,
                batch_size=args.batch_size,
                retry_failed=args.retry_failed
            )
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            sys.exit(0) 