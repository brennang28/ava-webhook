
import json
import os
from unittest.mock import MagicMock, patch
from src.ava_webhook.watcher import AvaWatcher

def test_payload_inspection():
    watcher = AvaWatcher()
    
    # Mock job data matching what Playbill would return
    test_job = {
        "company": "McCorkle Casting LTD",
        "role": "Casting Assistant Position – New York City-McCorkle Casting, Ltd.",
        "link": "https://www.playbill.com/job/casting-assistant-position-new-york-city-mccorkle-casting-ltd/0000018e-4a15-925b-6690-386ebb58"
    }
    
    with patch('requests.post') as mock_post:
        watcher.dispatch(test_job)
        
        # Capture the payload
        args, kwargs = mock_post.call_args
        payload = kwargs.get('json')
        
        print("WEBHOOK PAYLOAD SENT:")
        print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    test_payload_inspection()
