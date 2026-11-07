import os

TEST_ENVIRONMENT = {
    "AI_PROVIDER": "gemini",
    "GEMINI_API_KEY": "test-gemini-key",
    "GEMINI_MODEL": "gemini-3.8-flash",
    "GROQ_API_KEY": "test-groq-key",
    "GROQ_MODEL": "openai/gpt-oss-20b",
    "CEREBRAS_API_KEY": "test-cerebras-key",
    "CEREBRAS_MODEL": "gpt-oss-120b",
    "COHERE_API_KEY": "test-cohere-key",
    "COHERE_MODEL": "command-a-plus-05-2026",
    "CLOUDFLARE_API_TOKEN": "test-cloudflare-token",
    "CLOUDFLARE_ACCOUNT_ID": "0123456789abcdef0123456789abcdef",
    "CLOUDFLARE_MODEL": "@cf/zai-org/glm-4.7-flash",
    "NVIDIA_API_KEY": "test-nvidia-key",
    "NVIDIA_MODEL": "nvidia/nemotron-3.5-bolt-e4b",
    "OPENROUTER_API_KEY": "test-openrouter-key",
    "OPENROUTER_MODEL": "openrouter/free",
}
os.environ.update(TEST_ENVIRONMENT)

import pytest
import httpx

from main import create_app
from providers.base import ProviderError
from settings import Settings


class FakeProvider:
    model = "test-model"

    def __init__(self, answer: str = "A mocked answer.", failure: Exception | None = None):
        self.answer = answer
        self.failure = failure
        self.calls: list[tuple[str, float]] = []

    async def complete(self, message: str, temperature: float) -> str:
        self.calls.append((message, temperature))
        if self.failure:
            raise self.failure
        return self.answer


async def no_sleep(_: float) -> None:
    return None


@pytest.fixture
def make_client():
    def factory(provider: FakeProvider | None = None):
        fake_provider = provider or FakeProvider()
        app = create_app(
            Settings(
                ai_provider="gemini",
                gemini_api_key="test-key",
                gemini_model="gemini-3.8-flash",
                _env_file=None,
            ),
            provider=fake_provider,
            retry_sleep=no_sleep,
            jitter_source=lambda: 0.0,
        )
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )
        return client, fake_provider

    return factory


__all__ = ["FakeProvider", "ProviderError", "httpx"]
