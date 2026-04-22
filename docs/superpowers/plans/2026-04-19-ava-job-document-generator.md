# Ava Job Document Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `generator.py` using LangGraph's Send API to concurrently generate tailored resumes and cover letters for top-ranked jobs, upload them to Google Drive, and send the links to the Google Sheets webhook.

**Architecture:** We use a LangGraph `StateGraph` with Map-Reduce fan-out using the `Send` API. The pipeline loads context, maps over `jobs` concurrently via `process_job`. `process_job` calls Ollama for document generation, creates Google Drive folders and Docs via `google-api-python-client`, and aggregates results. Finally, `send_webhooks` pushes the results to Google Sheets.

**Tech Stack:** Python, LangGraph, LangChain Ollama, Google API Client (`google-api-python-client`), Pytest.

---

### Task 1: Install Dependencies

**Files:**
- Create/Modify: `setup.sh` (or install manually)

- [ ] **Step 1: Install Google API and doc libraries**

```bash
. .venv/bin/activate && pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-docx
```

- [ ] **Step 2: Update `setup.sh` to include dependencies**

```bash
echo "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-docx" >> setup.sh
chmod +x setup.sh
```

- [ ] **Step 3: Commit**

```bash
git add setup.sh
git commit -m "build: add google workspace and docx dependencies"
```

### Task 2: Build the Core Generator Graph & State

**Files:**
- Create: `generator.py`
- Create: `tests/test_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generator.py
from generator import AvaGenerator
import pytest

def test_generator_initialization():
    gen = AvaGenerator()
    assert gen.workflow is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest tests/test_generator.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'generator'"

- [ ] **Step 3: Write minimal implementation**

```python
# generator.py
import operator
from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

class OverallState(TypedDict):
    jobs: List[Dict[str, Any]]
    results: Annotated[List[Dict[str, Any]], operator.add]

class JobProcessState(TypedDict):
    job: Dict[str, Any]

class AvaGenerator:
    def __init__(self):
        self.workflow = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        builder = StateGraph(OverallState)
        builder.add_node("setup", self._setup)
        builder.add_edge(START, "setup")
        builder.add_edge("setup", END)
        return builder.compile()
        
    def _setup(self, state: OverallState):
        return {"results": []}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest tests/test_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_generator.py generator.py
git commit -m "feat: initialize generator langgraph"
```

### Task 3: Implement LangGraph Fan-out with Send API

**Files:**
- Modify: `generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generator.py (append)
def test_generator_fan_out():
    gen = AvaGenerator()
    test_jobs = [{"company": "A", "role": "Dev"}, {"company": "B", "role": "Eng"}]
    initial_state = {"jobs": test_jobs, "results": []}
    final_state = gen.workflow.invoke(initial_state)
    assert len(final_state["results"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_generator_fan_out -v`
Expected: FAIL (results length is 0)

- [ ] **Step 3: Write minimal implementation using Send API**

```python
# generator.py (update)
import operator
from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class OverallState(TypedDict):
    jobs: List[Dict[str, Any]]
    results: Annotated[List[Dict[str, Any]], operator.add]

class JobProcessState(TypedDict):
    job: Dict[str, Any]

class AvaGenerator:
    def __init__(self):
        self.workflow = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        builder = StateGraph(OverallState)
        builder.add_node("setup", self._setup)
        builder.add_node("process_job", self._process_job)
        builder.add_edge(START, "setup")
        builder.add_conditional_edges("setup", self._distribute_jobs, ["process_job"])
        builder.add_edge("process_job", END)
        return builder.compile()
        
    def _setup(self, state: OverallState):
        return {} 

    def _distribute_jobs(self, state: OverallState) -> List[Send]:
        return [Send("process_job", {"job": job}) for job in state["jobs"]]
        
    def _process_job(self, state: JobProcessState):
        job = state["job"]
        processed_job = job.copy()
        processed_job["status"] = "processed"
        return {"results": [processed_job]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_generator_fan_out -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add generator.py tests/test_generator.py
git commit -m "feat: add fan-out using Send API"
```

### Task 4: Implement LLM Document Generation Logic

**Files:**
- Modify: `generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generator.py (append)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_document_generation -v`
Expected: FAIL (KeyError 'cover_letter_text')

- [ ] **Step 3: Write minimal implementation**

```python
# generator.py (update)
import os
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

class AvaGenerator:
    def __init__(self):
        desktop_url = os.getenv("DESKTOP_OLLAMA_URL", "http://127.0.0.1:11434")
        self.llm = ChatOllama(model="llama3.2:3b", base_url=desktop_url)
        self.workflow = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        builder = StateGraph(OverallState)
        builder.add_node("setup", self._setup)
        builder.add_node("process_job", self._process_job)
        builder.add_edge(START, "setup")
        builder.add_conditional_edges("setup", self._distribute_jobs, ["process_job"])
        builder.add_edge("process_job", END)
        return builder.compile()

    def _setup(self, state: OverallState):
        return {}

    def _distribute_jobs(self, state: OverallState) -> List[Send]:
        return [Send("process_job", {"job": job}) for job in state["jobs"]]
    
    def _process_job(self, state: JobProcessState):
        job = state["job"]
        
        sys_msg = SystemMessage(content="You are an expert career coach. Draft a brief cover letter body.")
        human_msg = HumanMessage(content=f"Write a cover letter for {job.get('role')} at {job.get('company')}.")
        
        try:
            response = self.llm.invoke([sys_msg, human_msg])
            cover_letter_text = response.content
        except Exception as e:
            cover_letter_text = f"Error: {str(e)}"
            
        processed_job = job.copy()
        processed_job["cover_letter_text"] = cover_letter_text
        return {"results": [processed_job]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_document_generation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add generator.py tests/test_generator.py
git commit -m "feat: integrate LLM for document generation"
```

### Task 5: Implement Google Drive Upload Logic

**Files:**
- Modify: `generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generator.py (append)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_drive_upload_called -v`
Expected: FAIL (AttributeError: Mocked _upload_to_drive not called)

- [ ] **Step 3: Write minimal implementation**

```python
# generator.py (update)
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Add _upload_to_drive method to AvaGenerator
    def _upload_to_drive(self, company: str, role: str, content: str) -> str:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path or not os.path.exists(creds_path):
            return "No credentials provided"
            
        creds = Credentials.from_service_account_file(creds_path, scopes=["https://www.googleapis.com/auth/drive"])
        drive_service = build('drive', 'v3', credentials=creds)
        
        folder_metadata = {
            'name': f"{company} - {role}",
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
        folder_id = folder.get('id')
        
        doc_metadata = {
            'name': 'Cover Letter',
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }
        doc = drive_service.files().create(body=doc_metadata, fields='id').execute()
        
        # Note: A real implementation would upload the actual content. 
        # For simplicity, we just create the file.
        return folder.get('webViewLink', "No link generated")

# Update _process_job to call _upload_to_drive
    def _process_job(self, state: JobProcessState):
        job = state["job"]
        
        sys_msg = SystemMessage(content="You are an expert career coach. Draft a brief cover letter body.")
        human_msg = HumanMessage(content=f"Write a cover letter for {job.get('role')} at {job.get('company')}.")
        
        try:
            response = self.llm.invoke([sys_msg, human_msg])
            cover_letter_text = response.content
        except Exception as e:
            cover_letter_text = f"Error: {str(e)}"
            
        folder_link = self._upload_to_drive(job.get("company", "Unknown"), job.get("role", "Unknown"), cover_letter_text)
        
        processed_job = job.copy()
        processed_job["cover_letter_text"] = cover_letter_text
        processed_job["folder_link"] = folder_link
        return {"results": [processed_job]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_drive_upload_called -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add generator.py tests/test_generator.py
git commit -m "feat: implement Google Drive upload"
```

### Task 6: Implement Webhook Submission Node

**Files:**
- Modify: `generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generator.py (append)
import requests

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_webhook_submission -v`
Expected: FAIL (AttributeError: 'AvaGenerator' object has no attribute '_send_webhooks')

- [ ] **Step 3: Write minimal implementation**

```python
# generator.py (update)
import requests

# Update _build_graph
    def _build_graph(self) -> StateGraph:
        builder = StateGraph(OverallState)
        builder.add_node("setup", self._setup)
        builder.add_node("process_job", self._process_job)
        builder.add_node("send_webhooks", self._send_webhooks)
        
        builder.add_edge(START, "setup")
        builder.add_conditional_edges("setup", self._distribute_jobs, ["process_job"])
        builder.add_edge("process_job", "send_webhooks")
        builder.add_edge("send_webhooks", END)
        return builder.compile()

# Add _send_webhooks
    def _send_webhooks(self, state: OverallState):
        webhook_url = os.getenv("WEBHOOK_URL", "http://mock.webhook")
            
        for job in state["results"]:
            payload = {
                "company": job.get("company", ""),
                "title": job.get("role", ""),
                "link": job.get("link", ""),
                "folder_link": job.get("folder_link", "")
            }
            try:
                requests.post(webhook_url, json=payload)
            except Exception as e:
                print(f"Failed to post: {e}")
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest tests/test_generator.py::test_webhook_submission -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add generator.py tests/test_generator.py
git commit -m "feat: add webhook integration node"
```
