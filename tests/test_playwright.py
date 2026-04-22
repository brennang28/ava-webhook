from ava_webhook.watcher import AvaWatcher
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_playwright_verify():
    watcher = AvaWatcher()
    # Test with a known indeed link that was failing before (if possible)
    # Or just a general indeed job check
    test_links = [
        "https://www.indeed.com/viewjob?jk=81b7cdcfe19deba9",
        "https://www.linkedin.com/jobs/view/4401307744"
    ]
    
    print("Testing Playwright link verification...")
    for link in test_links:
        print(f"Verifying {link}...")
        result = watcher._verify_link(link)
        print(f"Result for {link}: {result}")
    
    watcher.close()

if __name__ == "__main__":
    test_playwright_verify()
