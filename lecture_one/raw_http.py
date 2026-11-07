"""Make the same chat-completion request with raw HTTP and httpx."""

from __future__ import annotations

from typing import Any

import httpx

from providers import OPENAI_COMPATIBLE_BASE_URLS
from settings import Settings


def ask_with_raw_http(message: str, settings: Settings) -> tuple[int, dict[str, Any]]:
    """Build the URL, bearer header, JSON body, and parse the response directly."""
    base_url = OPENAI_COMPATIBLE_BASE_URLS.get(settings.ai_provider)
    if base_url is None:
        raise ValueError(
            f"{settings.ai_provider} uses a native request format; choose Gemini, Groq, "
            "Cerebras, NVIDIA, or OpenRouter for this raw HTTP comparison."
        )

    response = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.active_api_key}"},
        json={
            "model": settings.active_model,
            "messages": [{"role": "user", "content": message}],
        },
        timeout=15.0,
    )
    print("Status:", response.status_code)
    print("Raw response:", response.text)
    response.raise_for_status()
    return response.status_code, response.json()


def main() -> None:
    settings = Settings()
    _, data = ask_with_raw_http("Explain APIs in simple language.", settings)
    print(f"data is {data}")
    print("Parsed answer:", data["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
