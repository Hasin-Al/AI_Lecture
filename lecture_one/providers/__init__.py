"""Provider registry and the small adapters used by the lecture project."""

from providers.base import Provider
from providers.cloudflare import CloudflareProvider
from providers.cohere import CohereProvider
from providers.openai_compatible import OpenAICompatibleProvider
from settings import Settings

OPENAI_COMPATIBLE_BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "groq": "https://api.groq.com/openai/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def get_provider(settings: Settings) -> Provider:
    if settings.ai_provider in OPENAI_COMPATIBLE_BASE_URLS:
        return OpenAICompatibleProvider(
            api_key=settings.active_api_key,
            model=settings.active_model,
            base_url=OPENAI_COMPATIBLE_BASE_URLS[settings.ai_provider],
        )
    if settings.ai_provider == "cohere":
        return CohereProvider(api_key=settings.active_api_key, model=settings.active_model)
    if settings.ai_provider == "cloudflare":
        return CloudflareProvider(
            api_token=settings.active_api_key,
            account_id=settings.cloudflare_account_id or "",
            model=settings.active_model,
        )
    raise ValueError(f"Unsupported provider: {settings.ai_provider}")


__all__ = ["get_provider"]
