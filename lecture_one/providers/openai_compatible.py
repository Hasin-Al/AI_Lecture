"""OpenAI chat-completions-compatible hosted provider adapter."""

from __future__ import annotations

import httpx

from providers.base import ProviderError


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._transport = transport

    async def complete(self, message: str, temperature: float) -> str:
        try:
            async with httpx.AsyncClient(timeout=45.0, transport=self._transport) as client:
                response = await client.post(
                    self._url,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self.model,
                        "temperature": temperature,
                        "messages": [{"role": "user", "content": message}],
                    },
                )
        except httpx.TimeoutException:
            raise
        except httpx.RequestError:
            raise ProviderError(502) from None

        if response.is_error:
            retryable = response.status_code == 429 or response.status_code >= 500
            raise ProviderError(
                response.status_code,
                response.headers.get("retry-after"),
                retryable=retryable,
            )
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError(502) from None
        if not isinstance(content, str) or not content.strip():
            raise ProviderError(502)
        return content.strip()
