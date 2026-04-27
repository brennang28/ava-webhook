import os
import json
from ava_webhook.scout import AvaScout
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

def test_scout_init():
    print("Testing AvaScout initialization and simple invoke")
    scout = AvaScout()
    print(f"LLM Base URL: {scout.llm.base_url}")
    print(f"LLM Client Kwargs: {scout.llm.client_kwargs}")
    
    # Try a simple invoke on the llm itself
    from langchain_core.messages import HumanMessage
    try:
        res = scout.llm.invoke([HumanMessage(content="hi")])
        print(f"LLM Success: {res.content[:50]}...")
    except Exception as e:
        print(f"LLM Failed: {e}")

    # Try the structured LLM
    try:
        # We need some dummy state for _score_jobs or just test invoke
        # Actually, let's just test with_structured_output directly
        res = scout.structured_llm.invoke([HumanMessage(content="Return a score for 1 job.")])
        print(f"Structured LLM Success: {res}")
    except Exception as e:
        print(f"Structured LLM Failed: {e}")

test_scout_init()
