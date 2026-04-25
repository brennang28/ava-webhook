import os
import requests
from dotenv import load_dotenv

load_dotenv()

cloud_url = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")
api_key = os.getenv("OLLAMA_AUX2_API_KEY")

headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

try:
    # Try common API endpoints
    for endpoint in ["/api/tags", "/api/models"]:
        resp = requests.get(f"{cloud_url}{endpoint}", headers=headers, timeout=10)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"Models at {endpoint}:")
            for m in models:
                print(f" - {m.get('name')}")
        else:
            print(f"Failed {endpoint}: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
