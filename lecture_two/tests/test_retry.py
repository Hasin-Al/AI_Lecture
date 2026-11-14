from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest
from groq import APITimeoutError, AuthenticationError, RateLimitError

from app.retry import retry_after_seconds, with_retry


def status_error(kind, status, headers=None):
    response = httpx.Response(status, headers=headers, request=httpx.Request("POST", "https://example.com"))
    return kind("simulated provider error", response=response, body=None)


def test_s14_rate_limit_then_success():
    calls, waits = [], []
    def flaky(remaining):
        calls.append(remaining)
        if len(calls) == 1:
            raise status_error(RateLimitError, 429, {"Retry-After": "2.5"})
        return "ok"
    assert with_retry(flaky, sleep=waits.append) == "ok"
    assert len(calls) == 2 and waits == [2.5]


@pytest.mark.parametrize("error", [
    status_error(AuthenticationError, 401),
    APITimeoutError(request=httpx.Request("POST", "https://example.com")),
])
def test_permanent_error_or_timeout_is_never_retried(error):
    calls = []
    def fails(remaining):
        calls.append(remaining)
        raise error
    with pytest.raises(type(error)):
        with_retry(fails, sleep=lambda _: pytest.fail("must not wait"))
    assert len(calls) == 1


def test_retry_attempt_limit():
    calls, waits = [], []
    def fails(remaining):
        calls.append(remaining)
        raise ConnectionError()
    with pytest.raises(ConnectionError):
        with_retry(fails, retry_on=(ConnectionError,), sleep=waits.append, jitter=lambda: 0)
    assert len(calls) == 3 and waits == [1, 2]


def test_retry_after_beyond_budget_does_not_retry_early():
    def fails(remaining):
        raise status_error(RateLimitError, 429, {"Retry-After": "120"})
    with pytest.raises(RateLimitError):
        with_retry(fails, sleep=lambda _: pytest.fail("budget exhausted"))


def test_http_date_retry_after():
    date = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=30), usegmt=True)
    error = status_error(RateLimitError, 429, {"Retry-After": date})
    assert 28 <= retry_after_seconds(error) <= 30


def test_elapsed_time_reduces_next_call_timeout():
    now, calls = [0], []
    def sleep(seconds):
        now[0] += seconds
    def flaky(remaining):
        calls.append(remaining)
        now[0] += 3
        if len(calls) == 1:
            raise ConnectionError()
        return "ok"
    assert with_retry(flaky, budget=10, sleep=sleep, clock=lambda: now[0],
                      jitter=lambda: 0, retry_on=(ConnectionError,)) == "ok"
    assert calls == [10, 6]
