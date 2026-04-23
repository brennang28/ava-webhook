import os
import logging
from ava_webhook.watcher import AvaWatcher
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_find_one_job():
    load_dotenv()
    watcher = AvaWatcher()
    
    try:
        # 1. Scrape Playbill (fastest source)
        logger.info("Scraping Playbill for a test job...")
        jobs = watcher.scrape_playbill()
        
        if not jobs:
            logger.info("No new jobs found on Playbill. Trying favorites...")
            jobs = watcher.scrape_favorites()
            
        if not jobs:
            logger.error("No new jobs found in any quick sources. Cannot test 'finding' a new job right now.")
            return

        # 2. Take the first new job
        test_job = jobs[0]
        logger.info(f"Found new job: {test_job['role']} @ {test_job['company']}")
        
        # 3. Dispatch to webhook
        # This will trigger the receiver.gs logic
        logger.info("Dispatching to webhook...")
        watcher.dispatch(test_job)
        
        # 4. Save to DB so we don't duplicate it again
        db_id = test_job.get('id') or test_job.get('link')
        watcher.save_job(db_id, test_job['role'], test_job['company'])
        
        logger.info("Test complete. Check your Google Sheet!")
        
    finally:
        watcher.close()

if __name__ == "__main__":
    test_find_one_job()
