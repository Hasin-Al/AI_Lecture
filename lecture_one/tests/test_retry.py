import asyncio

import httpx
import pytest

from providers.base import ProviderError
from retry import call_with_retry, retry_delay

pytestmark = pytest.mark.anyio


def test_retry_delay_uses_exponential_schedule_and_jitter_ceiling():
    assert retry_delay(0, None, 0.0) == 2.0
    assert retry_delay(1, None, 0.0) == 4.0
    assert retry_delay(2, None, 0.3) == 8.3


def test_retry_after_is_honored_up_to_the_cap():
    assert retry_delay(0, "4", 0.1) == 4.1
    assert retry_delay(0, "90", 0.1) == 8.1
    assert retry_delay(0, "not-a-number", 0.0) == 2.0


async def test_temporary_503_then_success_retries_with_backoff():
    attempts = 0
    waits = []

    async def operation():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ProviderError(503, retryable=True)
        return "recovered"

    async def no_sleep(seconds: float):
        waits.append(seconds)

    result = await call_with_retry(
        operation, sleep=no_sleep, jitter_source=lambda: 0.0
    )

    assert result == "recovered"
    assert attempts == 2
    assert waits == [2.0]


async def test_repeated_429_stops_after_three_attempts():
    attempts = 0
    waits = []

    async def operation():
        nonlocal attempts
        attempts += 1
        raise ProviderError(429, "3", retryable=True)

    async def no_sleep(seconds: float):
        waits.append(seconds)

    with pytest.raises(ProviderError) as error:
        await call_with_retry(operation, sleep=no_sleep, jitter_source=lambda: 0.0)

    assert error.value.status_code == 429
    assert attempts == 3
    assert waits == [3.0, 3.0]


@pytest.mark.parametrize(
    "failure",
    [
        ProviderError(401),
        ProviderError(502, retryable=False),
        httpx.ReadTimeout("provider timed out"),
    ],
    ids=["unauthorized", "malformed-response", "timeout"],
)
async def test_permanent_errors_and_timeouts_are_not_retried(failure):
    attempts = 0

    async def operation():
        nonlocal attempts
        attempts += 1
        raise failure

    async def no_sleep(_: float):
        raise AssertionError("non-retryable errors must not wait")

    with pytest.raises(type(failure)):
        await call_with_retry(operation, sleep=no_sleep)

    assert attempts == 1


async def test_total_deadline_stops_a_slow_provider_call():
    async def operation():
        await asyncio.sleep(0.05)
        return "too late"

    with pytest.raises(TimeoutError):
        await call_with_retry(operation, total_timeout=0.001)
