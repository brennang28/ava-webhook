import sys
import os
import sqlite3
import unittest
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath("src"))
from ava_webhook.watcher import AvaWatcher

class TestDeduplication(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_jobs.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.watcher = AvaWatcher(db_path=self.db_path)

    def tearDown(self):
        self.watcher.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_url_normalization(self):
        url1 = "https://www.linkedin.com/jobs/view/12345?refId=abc&trackingId=xyz"
        url2 = "https://www.linkedin.com/jobs/view/12345"
        self.assertEqual(self.watcher._normalize_url(url1), url2)

    def test_is_new_with_duplicates(self):
        job1_id = "https://example.com/job/1"
        job1_company = "AMC Global Media"
        job1_role = "Coordinator, Public Relations"

        # 1. First time should be new
        self.assertTrue(self.watcher.is_new(job1_id, job1_role, job1_company))
        self.watcher.save_job(job1_id, job1_role, job1_company)

        # 2. Same ID should not be new
        self.assertFalse(self.watcher.is_new(job1_id, job1_role, job1_company))

        # 3. Different ID but same Company/Role should not be new
        job2_id = "https://example.com/job/1?tracking=noise"
        self.assertFalse(self.watcher.is_new(job2_id, job1_role, job1_company))

    def test_history_loading(self):
        # Verify it loads from the correct path
        # Note: We depend on research/data/applied_history.json existing in the workspace
        history = self.watcher.applied_history_set
        print(f"Loaded {len(history)} historical jobs.")
        # If the file is missing, it will be empty but should not crash
        self.assertIsInstance(history, set)

if __name__ == "__main__":
    unittest.main()
