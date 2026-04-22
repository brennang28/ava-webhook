import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_model(model_name, base_url, api_key):
    print(f"Testing model: {model_name} at {base_url}...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "prompt": "Hi, are you working? Please respond with 'YES' and your model name.",
        "stream": False
    }
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            headers=headers,
            json=payload,
            timeout=30
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success ({duration:.2f}s): {result.get('response', '').strip()}")
            return True
        else:
            print(f"❌ Failed ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    cloud_url = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")
    api_key = os.getenv("OLLAMA_API_KEY")
    
    if not api_key:
        print("Error: OLLAMA_API_KEY not found in .env")
        exit(1)
        
    with open("config.json", "r") as f:
        config = json.load(f)
        
    models_to_test = []
    # Identify cloud models from config
    for key, val in config.get("models", {}).items():
        if ":cloud" in val:
            models_to_test.append(val)
            # Also test the base name without :cloud
            models_to_test.append(val.replace(":cloud", ""))
            
    # Deduplicate
    models_to_test = list(set(models_to_test))
    
    print(f"Models to test: {models_to_test}")
    for model in models_to_test:
        test_model(model, cloud_url, api_key)
