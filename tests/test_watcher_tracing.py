from ava_webhook.watcher import AvaWatcher


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


class DummyResponse:
    def __init__(self, status=200):
        self.status = status


class DummyPage:
    def __init__(self, html):
        self._html = html

    def goto(self, link, wait_until, timeout):
        return DummyResponse(status=200)

    def evaluate(self, script):
        return "Example company description"

    def wait_for_timeout(self, ms):
        return None

    def content(self):
        return self._html


class DummyContextManager:
    def __init__(self, page):
        self._page = page

    def new_page(self):
        return self._page

    def close(self):
        return None


class DummyBrowser:
    def __init__(self, page):
        self._page = page

    def new_context(self, user_agent=None):
        return DummyContextManager(self._page)


def test_verify_link_traces_tool_observation(monkeypatch):
    watcher = AvaWatcher()
    observation = DummyObservation()

    def mock_start_as_current_observation(name, as_type, input):
        assert name == "verify-link"
        assert as_type == "tool"
        assert input["link"] == "http://example.com"
        return DummyContext(observation)

    monkeypatch.setattr(watcher, "_get_browser", lambda: DummyBrowser(DummyPage("<html>example co</html>")))
    monkeypatch.setattr(watcher.langfuse, "start_as_current_observation", mock_start_as_current_observation)

    is_valid, description = watcher._verify_link("http://example.com", expected_company="Example Co")

    assert is_valid is True
    assert description == "Example company description"
    assert observation.output is not None
    assert observation.output["verified"] is True
    assert observation.output["status_code"] == 200
    assert observation.output["company_match"] is True
