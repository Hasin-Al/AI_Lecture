import pytest
from fastapi.testclient import TestClient
from groq import APITimeoutError, AuthenticationError, BadRequestError, RateLimitError
import httpx

from app.main import app, get_service
from app.groq_service import ExtractionFailure
from app.schemas import ContactExtraction


class FakeService:
    call_count = 1
    def __init__(self, **kwargs):
        pass
    def model_for(self, mode):
        return "offline-model"
    def extract(self, text, mode):
        return ContactExtraction(full_name="Mina Rahman", email="mina@example.com", phone=None)
    def extract_with_repair(self, text, mode):
        self.call_count = 2
        return self.extract(text, mode), True


@pytest.fixture
def client():
    app.dependency_overrides[get_service] = lambda: FakeService
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_health_and_docs_without_key(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    assert "/extract" in client.get("/openapi.json").json()["paths"]


@pytest.mark.parametrize("mode", ["prompt", "structured"])
@pytest.mark.parametrize("repair", [False, True])
def test_success(client, mode, repair):
    response = client.post("/extract", json={
        "text": "Mina Rahman mina@example.com", "mode": mode,
        "prompt_version": "v2", "repair": repair,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["schema_valid"] is True and body["repaired"] == repair
    assert body["provider_calls"] == (2 if repair else 1)
    assert body["prompt_version"] == "contact-extraction-v2"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert all(body["evidence"].values())


@pytest.mark.parametrize("payload", [
    {}, {"text": ""}, {"text": " \n"}, {"text": "x" * 8001},
    {"text": "Mina", "mode": "wrong"}, {"text": "Mina", "prompt_version": "v3"},
    {"text": "Mina", "admin": True}, {"text": 123},
])
def test_s10_bad_input_never_calls_model(client, payload, monkeypatch):
    monkeypatch.setattr(FakeService, "extract", lambda *a: pytest.fail("model called"))
    response = client.post("/extract", json=payload)
    assert response.status_code == 422
    assert response.headers["X-Request-ID"]


@pytest.mark.parametrize("error,status", [
    (ExtractionFailure("bad output"), 502),
    (ValueError("missing key"), 503),
    (APITimeoutError(request=httpx.Request("POST", "https://example.com")), 504),
    *[(kind("secret provider body", response=httpx.Response(code,
       request=httpx.Request("POST", "https://example.com")), body=None), expected)
      for kind, code, expected in [(AuthenticationError, 401, 502),
                                   (BadRequestError, 400, 502), (RateLimitError, 429, 503)]],
])
def test_safe_errors(client, monkeypatch, error, status):
    def fails(*args):
        raise error
    monkeypatch.setattr(FakeService, "extract", fails)
    response = client.post("/extract", json={"text": "Mina"})
    assert response.status_code == status
    assert "secret provider body" not in response.text
    assert response.json()["detail"]["request_id"] == response.headers["X-Request-ID"]
