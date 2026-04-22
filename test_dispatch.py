from watcher import AvaWatcher
import logging

# Setup logging to see output
logging.basicConfig(level=logging.INFO)

def manual_test():
    watcher = AvaWatcher()
    job = {
        "company": "Manual Test Corp",
        "role": "Senior Testing Specialist",
        "link": "https://example.com/test-result",
        "salary": "$200k"
    }
    print(f"Testing dispatch for: {job['role']}")
    watcher.dispatch(job)

if __name__ == "__main__":
    manual_test()
