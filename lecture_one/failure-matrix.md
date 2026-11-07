# Student Failure Matrix

Fill in **Observed** and **Pass** during the lecture. Use a mocked provider response for failures so the exercise does not depend on a real provider quota.

| Case | Expected result | Observed | Pass? |
|---|---|---|---|
| Empty message | HTTP 422; provider is not called |  |  |
| Temperature above 2 | HTTP 422; provider is not called |  |  |
| Invalid provider key | Provider 401 becomes safe HTTP 502; no retry |  |  |
| Provider rate limits every attempt | Three attempts, then safe HTTP 503 |  |  |
| Provider rate limit then success | Retry after bounded backoff; HTTP 200 |  |  |
| Provider read timeout | Safe HTTP 504; no retry |  |  |
| Provider returns malformed/empty response | Safe HTTP 502; no traceback or raw provider body |  |  |
| Backend stopped | Browser shows a network error and allows another attempt |  |  |
| Valid prompt | Answer and request ID appear in browser |  |  |
