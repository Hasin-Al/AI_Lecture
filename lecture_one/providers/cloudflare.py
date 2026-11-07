"""Cloudflare Workers AI adapter using the account-scoped REST endpoint."""

from __future__ import annotations

import httpx

from providers.base import ProviderError


class CloudflareProvider:
    def __init__(
        self,
        *,
        api_token: str,
        account_id: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self._api_token = api_token
        self._account_id = account_id
        self._transport = transport

    async def complete(self, message: str, temperature: float) -> str:
        url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self._account_id}/ai/run/{self.model}"
        )
        try:
            async with httpx.AsyncClient(timeout=15.0, transport=self._transport) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self._api_token}"},
                    json={
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
            data = response.json()
            if data.get("success") is False:
                raise ProviderError(502)
            content = data["result"]["response"]
        except ProviderError:
            raise
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ProviderError(502) from None
        if not isinstance(content, str) or not content.strip():
            raise ProviderError(502)
        return content.strip()
