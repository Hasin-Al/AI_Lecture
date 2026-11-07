"""Cohere Chat API adapter using its native v2 JSON contract."""

from __future__ import annotations

import httpx

from providers.base import ProviderError


class CohereProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._transport = transport

    async def complete(self, message: str, temperature: float) -> str:
        try:
            async with httpx.AsyncClient(timeout=15.0, transport=self._transport) as client:
                response = await client.post(
                    "https://api.cohere.com/v2/chat",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": message}],
                        "temperature": temperature,
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
            content_blocks = response.json()["message"]["content"]
            content = "".join(
                block["text"]
                for block in content_blocks
                if block.get("type") == "text" and isinstance(block.get("text"), str)
            )
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ProviderError(502) from None
        if not content.strip():
            raise ProviderError(502)
        return content.strip()
