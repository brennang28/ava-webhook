from watcher import AvaWatcher
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

class MockWatcher(AvaWatcher):
    def dispatch(self, job):
        role = job.get('role') or job.get('title') or 'Position'
        print(f"DEBUG: Mock Dispatch -> {role} @ {job.get('company', 'Unknown')}")
        return True

def test_scrape():
    watcher = MockWatcher()
    print("Testing Playbill scrape (Mocked Dispatch)...")
    watcher.scrape_playbill()
    # For general scrape, it might take longer and find nothing if results are old.
    # We'll just stick to Playbill for a quick check.

if __name__ == "__main__":
    test_scrape()
