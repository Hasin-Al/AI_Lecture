"""Small, bounded retry policy for temporary upstream rate/server errors."""

from __future__ import annotations

import asyncio
import math
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from providers.base import ProviderError

T = TypeVar("T")
Sleep = Callable[[float], Awaitable[None]]


def retry_delay(attempt: int, retry_after: str | None, jitter: float) -> float:
    """Calculate a capped exponential delay, honoring numeric Retry-After."""
    try:
        requested_wait = float(retry_after) if retry_after is not None else 2 ** (attempt + 1)
    except (TypeError, ValueError):
        requested_wait = 2 ** (attempt + 1)
    if not math.isfinite(requested_wait):
        requested_wait = 2 ** (attempt + 1)
    bounded_wait = min(max(requested_wait, 0.0), 8.0)
    bounded_jitter = min(max(jitter, 0.0), 0.3)
    return bounded_wait + bounded_jitter


async def call_with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    total_timeout: float = 45.0,
    sleep: Sleep = asyncio.sleep,
    jitter_source: Callable[[], float] = random.random,
) -> T:
    """Retry only explicitly retryable provider failures within one deadline."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if total_timeout <= 0:
        raise ValueError("total_timeout must be greater than 0")

    async with asyncio.timeout(total_timeout):
        for attempt in range(max_attempts):
            try:
                return await operation()
            except ProviderError as error:
                if not error.retryable or attempt + 1 >= max_attempts:
                    raise
                jitter = min(max(jitter_source(), 0.0), 1.0) * 0.3
                await sleep(retry_delay(attempt, error.retry_after, jitter))

    raise RuntimeError("retry loop ended without a result")
