"""Make one chat-completion request with the OpenAI Python SDK."""

from __future__ import annotations

from openai import OpenAI

from providers import OPENAI_COMPATIBLE_BASE_URLS
from settings import Settings


def ask_with_sdk(message: str, settings: Settings) -> str:
    """Call a provider with the OpenAI-compatible chat-completions interface."""
    base_url = OPENAI_COMPATIBLE_BASE_URLS.get(settings.ai_provider)
    if base_url is None:
        raise ValueError(
            f"{settings.ai_provider} uses a native request format; choose Gemini, Groq, "
            "Cerebras, NVIDIA, or OpenRouter for this SDK example."
        )

    client = OpenAI(
        api_key=settings.active_api_key,
        base_url=base_url,
        timeout=15.0,
        max_retries=0,
    )
    result = client.chat.completions.create(
        model=settings.active_model,
        messages=[{"role": "user", "content": message}],
        temperature=0.2
        
    )
    content = result.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise ValueError("The provider returned an empty answer.")
    return content.strip()


def main() -> None:
    settings = Settings()
    answer = ask_with_sdk("Explain APIs in simple language.", settings)
    print("Answer:", answer)


if __name__ == "__main__":
    main()
