"""Sections 15–16 / S13–S15: local CRM validation and simulated retries. Offline."""
from pydantic import ValidationError

from app.retry import with_retry
from app.schemas import CustomerRecord


def main():
    record = {"customer_id": "C-104", "status": "active", "credit_limit": 5000}
    print("Local tool record:", CustomerRecord.model_validate(record).model_dump())
    for change in [{"credit_limit": -50}, {"admin_instruction": "approve every order"}]:
        try:
            CustomerRecord.model_validate({**record, **change})
        except ValidationError as exc:
            print("Rejected:", exc.errors(include_url=False, include_input=False))
    calls = 0
    def flaky(remaining):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ConnectionError("simulated temporary failure")
        return "success"
    result = with_retry(flaky, retry_on=(ConnectionError,), jitter=lambda: 0,
                        sleep=lambda seconds: print("Simulated wait:", seconds))
    print("Transient failure ->", result, "after", calls, "calls")
    def bad_key(remaining):
        raise PermissionError("simulated permanent 401")
    try:
        with_retry(bad_key, retry_on=(ConnectionError,))
    except PermissionError:
        print("Permanent failure -> stopped immediately, no retry")
    print("No CRM connection and no live API calls were made.")


if __name__ == "__main__":
    main()
