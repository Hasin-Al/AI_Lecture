import httpx
import pytest

from tests.conftest import FakeProvider, ProviderError

pytestmark = pytest.mark.anyio


async def test_browser_page_is_served_from_same_origin(make_client):
    client, _ = make_client()

    async with client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="chat-form"' in response.text
    assert 'src="/static/app.js"' in response.text


async def test_health_returns_healthy(make_client):
    client, _ = make_client()

    async with client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_empty_message_is_rejected_before_provider_is_called(make_client):
    client, provider = make_client()

    async with client:
        response = await client.post("/chat", json={"message": "", "temperature": 5})

    assert response.status_code == 422
    assert provider.calls == []


async def test_valid_chat_returns_contract_and_request_id(make_client):
    client, provider = make_client(FakeProvider("A tiny lesson answer."))

    async with client:
        response = await client.post("/chat", json={"message": "What is HTTP?"})

    assert response.status_code == 200
    assert set(response.json()) == {"request_id", "response", "model"}
    assert response.json()["response"] == "A tiny lesson answer."
    assert response.json()["model"] == "test-model"
    assert response.json()["request_id"]
    assert provider.calls == [("What is HTTP?", 0.7)]


async def test_provider_timeout_returns_safe_504_with_request_id(make_client):
    client, _ = make_client(httpx_provider_timeout())

    async with client:
        response = await client.post("/chat", json={"message": "hi"})

    assert response.status_code == 504
    assert response.json()["detail"]["error"] == "AI provider timeout"
    assert response.json()["request_id"]


async def test_provider_401_becomes_safe_502_without_provider_details(make_client):
    client, _ = make_client(FakeProvider(failure=ProviderError(401)))

    async with client:
        response = await client.post("/chat", json={"message": "hi"})

    assert response.status_code == 502
    assert response.json()["detail"]["error"] == "AI provider request failed"
    assert "HTTP 401" not in response.text


async def test_provider_429_becomes_safe_503(make_client):
    client, provider = make_client(
        FakeProvider(failure=ProviderError(429, "2", retryable=True))
    )

    async with client:
        response = await client.post("/chat", json={"message": "hi"})

    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "AI provider rate limit exceeded"
    assert len(provider.calls) == 3


async def test_malformed_provider_response_becomes_safe_502(make_client):
    client, _ = make_client(FakeProvider(failure=ProviderError(502)))

    async with client:
        response = await client.post("/chat", json={"message": "hi"})

    assert response.status_code == 502
    assert response.json()["detail"]["error"] == "Unable to process AI provider response"
    assert "Traceback" not in response.text


async def test_summarize_returns_structured_summary(make_client):
    client, provider = make_client(FakeProvider("Short summary."))

    async with client:
        response = await client.post(
            "/summarize", json={"text": "A longer passage for the lesson."}
        )

    assert response.status_code == 200
    assert response.json()["summary"] == "Short summary."
    assert response.json()["request_id"]
    assert provider.calls[0][0].startswith("Summarize the following text")


def httpx_provider_timeout() -> FakeProvider:
    return FakeProvider(failure=httpx.ReadTimeout("slow provider"))
