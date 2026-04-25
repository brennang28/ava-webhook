import sys
import os
import json
import re
import unittest
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ava_webhook.watcher import AvaWatcher

class TestFiltering(unittest.TestCase):
    def setUp(self):
        # Create a mock config for testing
        self.config = {
            "filters": {
                "titles": ["Coordinator", "Associate"]
            },
            "exclusions": {
                "blocked_companies": ["BlockedCo"],
                "blocked_keywords": [
                    "Internship", "Intern", "Temporary", "Temp", "Contract", 
                    "Contractor", "Freelance"
                ]
            }
        }
        # Mock AvaWatcher to avoid DB/Playwright initialization
        self.watcher = AvaWatcher.__new__(AvaWatcher)
        self.watcher.config = self.config
        self.watcher.applied_history_set = set()

    def test_should_process_job(self):
        # Test cases: (title, company, job_type, expected_result)
        test_cases = [
            ("Marketing Coordinator", "GoodCo", "Full-time", True),
            ("Marketing Coordinator", "GoodCo", "Contract", False),
            ("Marketing Coordinator", "GoodCo", "Internship", False),
            ("Marketing Intern", "GoodCo", None, False), # Blocked by title
            ("Internship: Marketing", "GoodCo", None, False), # Blocked by title
            ("Internal Communications Coordinator", "GoodCo", "Full-time", True), # Should NOT match Intern
            ("Legal Counsel", "GoodCo", "Contract", False), # Blocked by metadata even if title is fine
            ("Temporary Admin", "GoodCo", None, False),
            ("Receptionist (Temp to Perm)", "GoodCo", None, False),
            ("Contract Writer", "GoodCo", None, False),
            ("Freelance Designer", "GoodCo", None, False),
            ("Junior Associate", "BlockedCo", "Full-time", False),
            ("Senior Manager", "GoodCo", "Full-time", False), # Existing filter for 'manager'
        ]

        for title, company, job_type, expected in test_cases:
            with self.subTest(title=title, company=company, job_type=job_type):
                result = AvaWatcher._should_process_job(self.watcher, title, company, job_type)
                self.assertEqual(result, expected, f"Failed for '{title}' @ '{company}' (Type: {job_type})")

if __name__ == "__main__":
    unittest.main()
