from ava_webhook.generator import AvaGenerator
import pytest
import requests

def test_generator_initialization():
    gen = AvaGenerator()
    assert gen.workflow is not None

def test_generator_fan_out():
    gen = AvaGenerator()
    test_jobs = [{"company": "A", "role": "Dev"}, {"company": "B", "role": "Eng"}]
    initial_state = {"jobs": test_jobs, "results": []}
    final_state = gen.workflow.invoke(initial_state)
    assert len(final_state["results"]) == 2

def test_document_generation(monkeypatch):
    class MockLLM:
        def invoke(self, messages):
            class MockResponse:
                content = "Mocked cover letter content"
            return MockResponse()

    gen = AvaGenerator()
    gen.llm = MockLLM()
    
    result = gen._process_job({"job": {"company": "TestCorp", "role": "Tester"}})
    assert result["results"][0]["cover_letter_text"] == "Mocked cover letter content"

def test_drive_upload_called(monkeypatch):
    upload_called = False
    
    def mock_upload(self, company, role, content):
        nonlocal upload_called
        upload_called = True
        return "http://mock-folder-link"

    monkeypatch.setattr(AvaGenerator, "_upload_to_drive", mock_upload)
    
    class MockLLM:
        def invoke(self, messages):
            class MockResponse:
                content = "Mocked cover letter content"
            return MockResponse()

    gen = AvaGenerator()
    gen.llm = MockLLM()
    
    result = gen._process_job({"job": {"company": "TestCorp", "role": "Tester"}})
    assert upload_called == True
    assert result["results"][0]["folder_link"] == "http://mock-folder-link"

def test_webhook_submission(monkeypatch):
    post_called = False
    def mock_post(url, json):
        nonlocal post_called
        post_called = True
        class MockResponse:
            status_code = 200
        return MockResponse()
        
    monkeypatch.setattr(requests, "post", mock_post)
    gen = AvaGenerator()
    gen._send_webhooks({"jobs": [], "results": [{"company": "A", "role": "B", "cover_letter_text": "text", "folder_link": "link"}]})
    assert post_called == True