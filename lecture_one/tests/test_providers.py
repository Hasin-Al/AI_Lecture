import asyncio
import json

import httpx

from providers.base import ProviderError
from providers.cloudflare import CloudflareProvider
from providers.cohere import CohereProvider
from providers.openai_compatible import OpenAICompatibleProvider
from providers import get_provider
from settings import Settings


def mock_transport(expected_url: str, response_json: dict):
    observed = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["method"] = request.method
        observed["url"] = str(request.url)
        observed["authorization"] = request.headers.get("authorization")
        observed["body"] = json.loads(request.content)
        assert observed["url"] == expected_url
        return httpx.Response(200, json=response_json)

    return httpx.MockTransport(handler), observed


def test_openai_compatible_provider_sends_chat_json_and_extracts_text():
    transport, observed = mock_transport(
        "https://api.groq.com/openai/v1/chat/completions",
        {
            "choices": [
                {"message": {"role": "assistant", "content": "An API is a contract."}}
            ]
        },
    )
    provider = OpenAICompatibleProvider(
        api_key="class-key",
        model="llama-demo",
        base_url="https://api.groq.com/openai/v1",
        transport=transport,
    )

    answer = asyncio.run(provider.complete("Explain API", 0.4))

    assert answer == "An API is a contract."
    assert observed["method"] == "POST"
    assert observed["authorization"] == "Bearer class-key"
    assert observed["body"]["model"] == "llama-demo"
    assert observed["body"]["temperature"] == 0.4
    assert observed["body"]["messages"] == [{"role": "user", "content": "Explain API"}]


def test_cohere_provider_sends_native_request_and_parses_text_blocks():
    transport, observed = mock_transport(
        "https://api.cohere.com/v2/chat",
        {
            "id": "response-1",
            "finish_reason": "COMPLETE",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Cohere native format."}],
            },
            "usage": {"billed_units": {"input_tokens": 2, "output_tokens": 3}},
        },
    )
    provider = CohereProvider(api_key="class-key", model="command-demo", transport=transport)

    answer = asyncio.run(provider.complete("Explain API", 0.4))

    assert answer == "Cohere native format."
    assert observed["body"]["model"] == "command-demo"
    assert observed["body"]["messages"][0]["content"] == "Explain API"


def test_cloudflare_provider_uses_account_scoped_result_shape():
    transport, observed = mock_transport(
        "https://api.cloudflare.com/client/v4/accounts/account-123/ai/run/@cf/demo",
        {"success": True, "errors": [], "result": {"response": "Cloudflare response."}},
    )
    provider = CloudflareProvider(
        api_token="class-token",
        account_id="account-123",
        model="@cf/demo",
        transport=transport,
    )

    answer = asyncio.run(provider.complete("Explain API", 0.4))

    assert answer == "Cloudflare response."
    assert observed["authorization"] == "Bearer class-token"


def test_malformed_or_empty_provider_response_raises_safe_error():
    transport, _ = mock_transport(
        "https://api.groq.com/openai/v1/chat/completions",
        {"choices": [{"message": {"content": " "}}]},
    )
    provider = OpenAICompatibleProvider(
        api_key="class-key",
        model="llama-demo",
        base_url="https://api.groq.com/openai/v1",
        transport=transport,
    )

    try:
        asyncio.run(provider.complete("Explain API", 0.4))
    except ProviderError as error:
        assert error.status_code == 502
        assert "class-key" not in str(error)
    else:
        raise AssertionError("empty assistant content must be rejected")


def test_provider_registry_maps_gemini_to_compatible_adapter():
    settings = Settings(
        ai_provider="gemini",
        gemini_api_key="class-key",
        gemini_model="gemini-3.8-flash",
        _env_file=None,
    )

    provider = get_provider(settings)

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == "gemini-3.8-flash"
