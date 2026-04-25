import unittest
from unittest.mock import MagicMock, patch
from ava_webhook.watcher import AvaWatcher, CLOSED_INDICATORS

class TestClosedDetection(unittest.TestCase):
    def setUp(self):
        # Mock config to avoid loading real file
        with patch('builtins.open', unittest.mock.mock_open(read_data='{"filters": {"titles": []}, "favorite_companies": [], "exclusions": {}}')):
            self.watcher = AvaWatcher(config_path="dummy.json")

    @patch('ava_webhook.watcher.sync_playwright')
    def test_verify_link_closed_detection(self, mock_playwright):
        # Setup mocks
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        mock_playwright.return_value.start.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        mock_page.goto.return_value = MagicMock(status=200)
        
        # 1. Test active job
        mock_page.content.return_value = "<html><body>Welcome to our job posting at Google</body></html>"
        result = self.watcher._verify_link("https://google.com/jobs/123", expected_company="Google")
        self.assertTrue(result, "Should return True for an active job with matching company")

        # 2. Test closed job (LinkedIn indicator)
        for indicator in CLOSED_INDICATORS:
            mock_page.content.return_value = f"<html><body>{indicator}</body></html>"
            result = self.watcher._verify_link("https://linkedin.com/jobs/123")
            self.assertFalse(result, f"Should return False when indicator '{indicator}' is present")

    def tearDown(self):
        self.watcher.close()

if __name__ == '__main__':
    unittest.main()
