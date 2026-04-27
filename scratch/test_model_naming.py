import os
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

api_key = os.getenv("OLLAMA_AUX2_API_KEY")
cloud_url = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")

def test_model(model_name):
    print(f"\nTesting model: {model_name}")
    llm = ChatOllama(
        model=model_name,
        base_url=cloud_url,
        headers={"Authorization": f"Bearer {api_key}"}
    )
    try:
        res = llm.invoke([HumanMessage(content="hi")])
        print(f"Success: {res.content[:50]}...")
    except Exception as e:
        print(f"Failed: {e}")

test_model("gemma4:31b")
test_model("gemma4:31b:cloud")
