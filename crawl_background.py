#!/usr/bin/env python3
"""
Background Crawler for Odoo 19 Documentation
Runs crawl in batches and saves progress
"""

import subprocess
import time
import sys
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawl_background.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_crawl_batch(batch_size=500):
    """Run a batch of crawling"""
    logger.info(f"Starting batch of {batch_size} pages...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'src.main', 'crawl', '--urls', 'urls.txt', '--max-pages', str(batch_size)],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per batch
        )
        
        logger.info("Batch completed")
        logger.debug(result.stdout)
        
        if result.stderr:
            logger.error(f"Errors: {result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.warning("Batch timed out, will retry")
        return True  # Continue to next batch
    except Exception as e:
        logger.error(f"Error in batch: {e}")
        return False

def check_status():
    """Check current crawl status"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'src.main', 'status'],
            capture_output=True,
            text=True,
            timeout=30
        )
        logger.info("Current status:\n" + result.stdout)
        
        # Parse queue size from output
        for line in result.stdout.split('\n'):
            if 'Queue Size:' in line:
                queue_size = int(line.split(':')[1].strip())
                return queue_size
        return None
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return None

def main():
    """Main background crawl loop"""
    logger.info("=" * 60)
    logger.info("Starting Background Crawler for Odoo 19 Documentation")
    logger.info("=" * 60)
    
    batch_size = 500
    max_retries = 3
    retry_count = 0
    
    while True:
        # Check current status
        queue_size = check_status()
        
        if queue_size is None:
            logger.error("Could not determine queue size, waiting...")
            time.sleep(60)
            continue
            
        if queue_size == 0:
            logger.info("=" * 60)
            logger.info("CRAWL COMPLETED! All pages processed.")
            logger.info("=" * 60)
            break
        
        logger.info(f"Queue size: {queue_size} pages remaining")
        
        # Run a batch
        success = run_crawl_batch(batch_size)
        
        if success:
            retry_count = 0
            logger.info(f"Batch successful. Waiting 10 seconds before next batch...")
            time.sleep(10)
        else:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Max retries ({max_retries}) reached. Stopping.")
                break
            logger.warning(f"Batch failed. Retry {retry_count}/{max_retries} in 60 seconds...")
            time.sleep(60)
    
    # Final status
    logger.info("Final status:")
    check_status()

if __name__ == '__main__':
    main()
