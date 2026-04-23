import logging
import json
import os
from ava_webhook.watcher import AvaWatcher
from ava_webhook.scout import AvaScout
from ava_webhook.generator import AvaGenerator
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load env
load_dotenv()

def find_one_full_pipeline():
    watcher = AvaWatcher()
    scout = AvaScout()
    generator = AvaGenerator()
    try:
        logger.info("Scraping for candidates...")
        
        # Collect candidates from all sources to ensure we have something to rank
        pool = []
        pool.extend(watcher.scrape_playbill())
        pool.extend(watcher.scrape_general())
        
        if not pool:
            print("No new jobs found currently.")
            return

        logger.info(f"Found {len(pool)} candidates. Ranking...")
        
        # Use scout to find the top job
        top_jobs = scout.rank(pool, limit=1)
        
        if top_jobs:
            new_job = top_jobs[0]
            print("\n--- TOP JOB SELECTED ---")
            print(f"Company: {new_job.get('company')}")
            print(f"Role:    {new_job.get('role')}")
            print(f"Score:   {new_job.get('relevance_score')}")
            print(f"Reason:  {new_job.get('relevance_reason')}")
            print(f"Link:    {new_job.get('link')}")
            print("----------------------\n")
            
            # Run generator for this job
            print("--- GENERATING DOCUMENTS ---")
            generator.workflow.invoke({"jobs": [new_job], "results": []})
            
            # Save to DB
            db_id = new_job.get('id') or new_job.get('link')
            watcher.save_job(db_id, new_job['role'], new_job['company'])
            print("--- DONE ---")
        else:
            print("No jobs passed the relevance threshold.")
            
    finally:
        watcher.close()

if __name__ == "__main__":
    find_one_full_pipeline()
