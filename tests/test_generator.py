from ava_webhook.generator import AvaGenerator
from google.auth.exceptions import RefreshError
import pytest
import requests
import os
import io

def test_generator_initialization():
    gen = AvaGenerator()
    assert gen.workflow is not None

def test_generator_fan_out():
    gen = AvaGenerator()
    test_jobs = [{"company": "A", "role": "Dev"}, {"company": "B", "role": "Eng"}]
    initial_state = {"jobs": test_jobs, "results": []}
    final_state = gen.workflow.invoke(initial_state)
    assert len(final_state["results"]) >= 1

def test_document_generation(monkeypatch):
    class MockLLM:
        def __init__(self):
            self.model = "mock-model"

        def invoke(self, messages):
            class MockResponse:
                content = "Mocked cover letter content"
            return MockResponse()

    gen = AvaGenerator()
    gen.llm = MockLLM()
    gen.reasoning_llm = MockLLM()

    result = gen._process_jobs_sequentially({"jobs": [{"company": "TestCorp", "role": "Tester"}], "results": []})
    assert len(result["results"]) >= 1

def test_drive_upload_called(monkeypatch):
    upload_called = False

    def mock_upload(self, company, role, cover_buffer, resume_buffer):
        nonlocal upload_called
        upload_called = True
        return "http://mock-folder-link"

    monkeypatch.setattr(AvaGenerator, "_upload_to_drive", mock_upload)

    class MockLLM:
        def __init__(self):
            self.model = "mock-model"

        def invoke(self, messages):
            class MockResponse:
                content = "Mocked cover letter content"
            return MockResponse()

    gen = AvaGenerator()
    gen.llm = MockLLM()
    gen.reasoning_llm = MockLLM()

    result = gen._process_jobs_sequentially({"jobs": [{"company": "TestCorp", "role": "Tester"}], "results": []})
    assert upload_called == True

class DummyObservation:
    def __init__(self):
        self.output = None
    def update(self, *, output=None, **kwargs):
        self.output = output

class DummyContext:
    def __init__(self, observation):
        self.observation = observation
    def __enter__(self):
        return self.observation
    def __exit__(self, exc_type, exc, tb):
        return False


def test_upload_to_drive_traces_tool_observation(monkeypatch, tmp_path):
    obs = DummyObservation()

    def mock_with_tool_observation(self, name, input_data):
        return DummyContext(obs)

    monkeypatch.setattr(AvaGenerator, "_with_tool_observation", mock_with_tool_observation)
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    gen = AvaGenerator()
    result = gen._upload_to_drive("TestCo", "Engineer", io.BytesIO(b"cov"), io.BytesIO(b"res"))

    assert "Saved locally only" in result
    assert obs.output is not None
    assert obs.output["local_backup"] is True
    assert obs.output["drive_upload"] is False
    assert obs.output["folder_created"] is False
    assert obs.output["cover_letter_uploaded"] is False
    assert obs.output["resume_uploaded"] is False
    assert obs.output["error"] == "token.json missing"


def test_upload_to_drive_refreshes_expired_token(monkeypatch, tmp_path):
    class DummyObservation:
        def __init__(self):
            self.output = None
        def update(self, *, output=None, **kwargs):
            self.output = output

    class DummyContext:
        def __init__(self, observation):
            self.observation = observation
        def __enter__(self):
            return self.observation
        def __exit__(self, exc_type, exc, tb):
            return False

    refreshed = False

    def mock_with_tool_observation(self, name, input_data):
        return DummyContext(DummyObservation())

    class FakeCreds:
        def __init__(self):
            self.valid = False
            self.expired = True
            self.refresh_token = 'refresh-token'
        def refresh(self, request):
            nonlocal refreshed
            refreshed = True
            self.valid = True
            self.expired = False
        def to_json(self):
            return '{"refreshed": true}'

    class FakeFiles:
        def create(self, body, media_body=None, fields=None):
            class FakeRequest:
                def execute(self):
                    return {'id': 'fake-id', 'webViewLink': 'https://drive.fake/folder'}
            return FakeRequest()

    class FakeDriveService:
        def files(self):
            return FakeFiles()

    monkeypatch.setattr(AvaGenerator, "_with_tool_observation", mock_with_tool_observation)
    monkeypatch.setattr('ava_webhook.generator.Credentials.from_authorized_user_file', lambda path, scopes: FakeCreds())
    monkeypatch.setattr('ava_webhook.generator.build', lambda service, version, credentials=None: FakeDriveService())

    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('token.json').write_text('{}')

    gen = AvaGenerator()
    result = gen._upload_to_drive("TestCo", "Engineer", io.BytesIO(b"cov"), io.BytesIO(b"res"))

    assert refreshed is True
    assert 'https://drive.fake/folder' in result
    assert tmp_path.joinpath('token.json').read_text() == '{"refreshed": true}'


def test_upload_to_drive_refresh_error_returns_local_only(monkeypatch, tmp_path):
    class DummyObservation:
        def __init__(self):
            self.output = None
        def update(self, *, output=None, **kwargs):
            self.output = output

    class DummyContext:
        def __init__(self, observation):
            self.observation = observation
        def __enter__(self):
            return self.observation
        def __exit__(self, exc_type, exc, tb):
            return False

    def mock_with_tool_observation(self, name, input_data):
        return DummyContext(DummyObservation())

    class FakeCreds:
        def __init__(self):
            self.valid = False
            self.expired = True
            self.refresh_token = 'refresh-token'
        def refresh(self, request):
            raise RefreshError('invalid_grant: Token has been expired or revoked.')

    monkeypatch.setattr(AvaGenerator, "_with_tool_observation", mock_with_tool_observation)
    monkeypatch.setattr('ava_webhook.generator.Credentials.from_authorized_user_file', lambda path, scopes: FakeCreds())

    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath('token.json').write_text('{}')

    gen = AvaGenerator()
    result = gen._upload_to_drive("TestCo", "Engineer", io.BytesIO(b"cov"), io.BytesIO(b"res"))

    assert "Drive auth failed" in result
    assert "setup_oauth.py" in result


def test_run_drive_step_observation(monkeypatch):
    called_names = []

    def mock_with_tool_observation(self, name, input_data):
        called_names.append(name)
        return DummyContext(DummyObservation())

    monkeypatch.setattr(AvaGenerator, "_with_tool_observation", mock_with_tool_observation)

    gen = AvaGenerator()
    result = gen._run_drive_step(
        "create-folder",
        {"company": "TestCo", "role": "Engineer"},
        lambda: {"id": "folder123"}
    )

    assert result == {"id": "folder123"}
    assert called_names == ["upload-to-drive/create-folder"]


def test_webhook_submission(monkeypatch):
    post_called = False
    def mock_post(url, json=None, timeout=None):
        nonlocal post_called
        post_called = True
        class MockResponse:
            status_code = 200
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)
    gen = AvaGenerator()
    gen._send_webhooks({"jobs": [], "results": [{"company": "A", "role": "B", "cover_letter_text": "text", "folder_link": "link"}]})
    assert post_called == True