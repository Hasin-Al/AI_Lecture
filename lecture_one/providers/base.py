"""Provider boundary shared by all model API adapters."""

from __future__ import annotations

from typing import Protocol


class ProviderError(Exception):
    """Safe upstream failure details used for mapping errors in the API layer."""

    def __init__(
        self,
        status_code: int,
        retry_after: str | None = None,
        *,
        retryable: bool = False,
    ) -> None:
        self.status_code = status_code
        self.retry_after = retry_after
        self.retryable = retryable
        super().__init__(f"AI provider returned HTTP {status_code}")


class Provider(Protocol):
    model: str

    async def complete(self, message: str, temperature: float) -> str: ...
