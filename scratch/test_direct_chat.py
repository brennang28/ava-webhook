import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OLLAMA_AUX2_API_KEY")
cloud_url = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")
headers = {"Authorization": f"Bearer {api_key}"}

payload = {
    "model": "gemma4:31b",
    "messages": [
        {"role": "user", "content": "hi"}
    ],
    "stream": False
}

print(f"Testing direct POST to {cloud_url}/api/chat")
try:
    resp = requests.post(f"{cloud_url}/api/chat", headers=headers, json=payload, timeout=60)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Success: {resp.json().get('message', {}).get('content', '')[:50]}...")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Failed: {e}")
