import os
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import logging

# logging.basicConfig(level=logging.INFO)
load_dotenv()

api_key = os.getenv("OLLAMA_AUX2_API_KEY")
cloud_url = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")

def test_fixed_client():
    print(f"Testing ChatOllama with client_kwargs for headers")
    # Set num_predict in constructor instead of invoke
    llm = ChatOllama(
        model="gemma4:31b",
        base_url=cloud_url,
        num_predict=10,
        client_kwargs={"headers": {"Authorization": f"Bearer {api_key}"}}
    )
    try:
        res = llm.invoke([HumanMessage(content="hi")])
        print(f"Success! Response: {res.content}")
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

test_fixed_client()
