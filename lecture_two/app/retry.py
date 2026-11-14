"""Provider retries are separate from the single output-quality repair."""
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from groq import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

TRANSIENT = (APIConnectionError, InternalServerError, RateLimitError)


def retry_after_seconds(exc) -> float | None:
    response = getattr(exc, "response", None)
    value = response.headers.get("retry-after") if response is not None else None
    if not value:
        return None
    try:
        return max(0, float(value))
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
            return max(0, (date - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return None


def with_retry(fn, attempts=3, budget=45.0, sleep=time.sleep,
               clock=time.monotonic, jitter=lambda: random.uniform(0, 0.3),
               retry_on=TRANSIENT):
    """fn receives the remaining seconds so the SDK can shorten its timeout.

    Stop starting retries after the budget. HTTP timeouts limit individual I/O
    waits, so this is a retry scheduling budget, not hard wall-clock cancellation.
    """
    if attempts < 1 or budget <= 0:
        raise ValueError("attempts and budget must be positive")
    deadline = clock() + budget
    for attempt in range(attempts):
        try:
            return fn(max(0.001, deadline - clock()))
        except APITimeoutError:
            # Timeout subclasses APIConnectionError. Catch it FIRST.
            raise
        except retry_on as exc:
            delay = retry_after_seconds(exc)
            if delay is None:
                delay = min(2 ** attempt, 8) + jitter()
            if attempt == attempts - 1 or clock() + delay >= deadline:
                raise
            sleep(delay)
