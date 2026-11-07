# Week 1 API-First Python Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a classroom-ready Python lab that follows the Week 1 notes from the first HTTP request through a tested FastAPI AI proxy, browser UI, and `/summarize` homework route.

**Architecture:** One evolving project with standalone early examples and a final FastAPI app. A shared provider interface dispatches to OpenAI-compatible endpoints or provider-specific adapters, while settings load secrets from `.env`; tests exercise the app with mocked upstream HTTP calls.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic Settings, httpx, OpenAI-compatible Python client, plain HTML/CSS/JavaScript, pytest, `httpx.MockTransport`, python-dotenv.

**Spec:** `docs/superpowers/specs/2026-11-06-week-one-api-first-python-lab-design.md`

## Global Constraints

- Provider keys live only in `.env` or the hosting environment; `.env` is ignored by Git.
- The browser calls only the same-origin FastAPI API and never receives a provider key.
- Every network request has an explicit timeout.
- Provider errors are normalized to safe messages and carry a request ID; secrets, prompts, tracebacks, and raw provider bodies are not logged or returned.
- Retry only transient 429/5xx responses, with a bounded attempt count, total deadline, jitter, and `Retry-After` support; do not retry timeouts or permanent 4xx responses.
- Mock upstream calls in tests; no test requires real provider credentials or incurs API usage.
- Render model output through `textContent`.
- Initial provider profiles: Gemini, Groq, Cerebras, Cohere trial, Cloudflare Workers AI, NVIDIA NIM hosted prototyping, and OpenRouter free models. Provider quotas, models, account eligibility, and terms can change.
- The walkthrough must map demos, instructor prompts, and learner exercises to all sections 1–14 of the supplied notes.

## Review Focus

- Missing or malformed provider configuration must fail with a clear startup/settings error before a lesson silently makes a real request. Add settings tests for missing selected-provider key and valid selected-provider configuration in Task 2.
- Empty and oversized user messages, invalid temperatures, and malformed JSON must be rejected before calling the provider. Add request contract tests for 422 and zero upstream calls in Task 3.
- Provider response drift (missing choices/content, empty text, native Cohere/Cloudflare response shape) must become a normalized 502 response with a request ID and no raw internals. Add response parsing and malformed response tests in Tasks 2 and 5.
- Retry behavior must not repeat timeouts or non-transient 4xx responses and must stop within the configured budget. Add retry cases for 401, repeated 429, 503 then success, and timeout in Task 5.
- The browser must remain safe and usable for non-2xx, non-JSON, network-down, and HTML-like model output cases. Add UI behavior review/example cases to Task 4 and document manual Network-tab and stopped-backend exercises in Task 6.

---

### Task 1: Project setup and first HTTP/JSON request

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `first_request.py`
- Create: `tests/test_first_request.py`

**Interfaces:**
- Produces: `send_echo_request(method: str = "POST") -> tuple[int, dict]` in `first_request.py`; supports POST and GET to httpbin with a 10-second timeout.
- `first_request.py` can be run directly and prints status and parsed JSON.

- [x] **Step 1: Write tests for the echo request helper**

Test POST and GET using a patched `httpx` transport. Assert the expected method, timeout, status, and parsed JSON result.

- [x] **Step 2: Run the focused tests to confirm they fail because the helper is missing**

Run: `python -m pytest tests/test_first_request.py -q`
Expected: FAIL because `send_echo_request` does not exist.

- [x] **Step 3: Implement the helper and direct-run output**

Use `httpx` with JSON payload for POST, no body for GET, and an explicit 10-second timeout.

- [x] **Step 4: Run the focused tests and confirm they pass**

Run: `python -m pytest tests/test_first_request.py -q`
Expected: PASS for POST and GET.

- [x] **Step 5: Add dependencies, secret-safe `.gitignore`, and `.env.example`**

Declare the libraries used by later tasks. Ignore `.env`, Python caches, virtual environments, and pytest caches. Keep all example key values empty/placeholders.

### Task 2: Settings and provider adapters

**Files:**
- Create: `settings.py`
- Create: `providers/__init__.py`
- Create: `providers/base.py`
- Create: `providers/openai_compatible.py`
- Create: `providers/cohere.py`
- Create: `providers/cloudflare.py`
- Create: `tests/test_settings.py`
- Create: `tests/test_providers.py`
- Modify: `.env.example`

**Interfaces:**
- Consumes: dependency declarations from Task 1.
- Produces: `Settings` with `ai_provider`, per-provider key/model configuration, and Cloudflare account ID; `Provider.complete(message: str, temperature: float) -> str`; `get_provider(settings) -> Provider`.
- Provider names are `gemini`, `groq`, `cerebras`, `cohere`, `cloudflare`, `nvidia`, and `openrouter`.

- [x] **Step 1: Write settings tests for valid and missing selected-provider configuration**

Assert each selected provider requires its corresponding credential (and Cloudflare account ID) and that configured model/base URL values are available to the adapter.

- [x] **Step 2: Run settings tests to confirm they fail because settings are missing**

Run: `python -m pytest tests/test_settings.py -q`
Expected: FAIL because `Settings` is not defined.

- [x] **Step 3: Implement settings using Pydantic Settings and `.env` loading**

Use a per-provider optional key and model setting so students only need to create one provider key. Select one documented no-cost default profile in `.env.example`, with an empty key field.

- [x] **Step 4: Write provider adapter tests against mocked `httpx` transport**

Cover one OpenAI-compatible adapter profile, Cohere's native response shape, Cloudflare's account-scoped response shape, missing/empty text, upstream error status, and request timeout propagation.

- [x] **Step 5: Run provider tests to confirm they fail because adapters are missing**

Run: `python -m pytest tests/test_providers.py -q`
Expected: FAIL because provider implementations are not defined.

- [x] **Step 6: Implement provider protocol, registry, and three adapter paths**

Route Gemini/Groq/Cerebras/NVIDIA/OpenRouter through documented OpenAI-compatible chat completions endpoints. Use dedicated parsers for Cohere and Cloudflare. Return only assistant text or raise a typed provider error; do not include credentials or raw response bodies in exceptions.

- [x] **Step 7: Run settings and provider tests**

Run: `python -m pytest tests/test_settings.py tests/test_providers.py -q`
Expected: PASS, including native response parsing and empty-response rejection.

### Task 3: Contracts and FastAPI proxy

**Files:**
- Create: `schemas.py`
- Create: `main.py`
- Create: `tests/conftest.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Consumes: `get_provider(settings)` from Task 2.
- Produces: `GET /health`, `POST /chat`, and `POST /summarize`; `ChatRequest(message: str, temperature: float = 0.7)` validates message length 1–4000 and temperature 0–2; `ChatResponse(request_id: str, response: str, model: str)`.
- `/chat` and `/summarize` return request IDs and normalized error objects.

- [x] **Step 1: Write contract and route tests for health, validation, success, timeout, rate limit, and provider failures**

Assert invalid input yields 422 without calling the provider; success has exactly the documented response fields and request ID; timeout maps to 504, upstream 429 maps to 503, other provider errors/malformed output map to 502.

- [x] **Step 2: Configure dummy settings before importing the app in tests**

Set test-only provider/model values in `tests/conftest.py`, then create an async `httpx.AsyncClient` fixture using `httpx.ASGITransport(app=app)`.

- [x] **Step 3: Run API tests to confirm they fail because schemas/routes are missing**

Run: `python -m pytest tests/test_api.py -q`
Expected: FAIL because `main.app` is not defined.

- [x] **Step 4: Implement Pydantic request and response models**

Use the exact bounds and defaults in the Interfaces block. Define the safe error response shape with `request_id` and `detail.error`.

- [x] **Step 5: Implement health and chat routes with request IDs and safe structured logs**

Log request start, completion/failure, provider name, and request ID only; do not log message text, credentials, authorization headers, traceback, or raw upstream body.

- [x] **Step 6: Implement `/summarize` with bounded input and structured summary output**

Validate non-empty text up to 12,000 characters. Ask the configured provider for a concise summary and return request ID, summary, and model through a response schema.

- [x] **Step 7: Run API tests and confirm validation, response shape, and normalized errors**

Run: `python -m pytest tests/test_api.py -q`
Expected: PASS with no real upstream calls.

### Task 4: Browser teaching UI

**Files:**
- Create: `static/index.html`
- Create: `static/app.js`
- Create: `static/styles.css`
- Modify: `main.py`

- **Interfaces:**
- Consumes: `POST /chat` and `POST /summarize` response contracts from Task 3.
- Produces: same-origin `/` page with prompt form, temperature selector, answer/error area, and request ID display.

- [x] **Step 1: Add a route that serves the static page from the FastAPI app**

Keep browser and API same-origin; do not add provider credentials or call provider domains from JavaScript.

- [x] **Step 2: Implement idle, loading, success, and error states using `fetch`**

Disable submit while loading, check `response.ok`, handle non-JSON/network errors, and re-enable input after either result.

- [x] **Step 3: Render every answer and error with `textContent`**

Show the returned request ID on success and when a normalized API error includes one.

- [x] **Step 4: Review the browser flow against the defined manual cases**

Confirm valid prompt, validation failure, backend offline, non-2xx response, and HTML-like response text remain readable and safe. Document these cases in the README; do not add a frontend test framework.

### Task 5: Bounded retries and failure test matrix

**Files:**
- Create: `retry.py`
- Create: `tests/test_retry.py`
- Modify: `providers/openai_compatible.py`
- Modify: `providers/cohere.py`
- Modify: `providers/cloudflare.py`
- Modify: `tests/test_api.py`
- Create: `failure-matrix.md`

**Interfaces:**
- Consumes: typed provider errors from Task 2 and route error mapping from Task 3.
- Produces: `retry_delay(attempt: int, retry_after: str | None, jitter: float) -> float` and `call_with_retry(operation, max_attempts=3, total_timeout=45)` for async provider calls.

- [x] **Step 1: Write retry policy tests**

Assert 401/400 are never retried; read timeout is never retried; 429 and 5xx retry at most three total attempts; `Retry-After` is used when numeric; waits cap at 8 seconds before jitter; exhausted retries map to 503.

- [x] **Step 2: Run retry tests to confirm they fail because retry policy is missing**

Run: `python -m pytest tests/test_retry.py -q`
Expected: FAIL because retry helpers are not defined.

- [x] **Step 3: Implement retry delay and async retry budget**

Use exponential waits of 2, 4, and 8 seconds, a 0.3-second jitter ceiling, a maximum of three attempts, and an overall 45-second deadline. Make sleep and jitter injectable for deterministic tests.

- [x] **Step 4: Integrate retries only for upstream 429 and 5xx responses**

Do not retry network/read timeouts, malformed responses, or other 4xx responses. Preserve request ID across attempts and avoid logging prompt or secret material.

- [x] **Step 5: Complete provider failure matrix tests**

Add malformed response, repeated 429, 503 then success, timeout, and provider 401 cases to API-level tests; assert upstream call counts and safe outward response.

- [x] **Step 6: Create the blank learner failure matrix**

Include empty message, invalid key, repeated rate limit, rate limit then success, timeout, malformed response, backend stopped, and valid prompt with Expected/Observed/Pass columns.

- [x] **Step 7: Run the mocked failure tests**

Run: `python -m pytest tests/test_retry.py tests/test_api.py -q`
Expected: PASS; no real provider call or real retry sleep occurs.

### Task 6: Instructor runbook, free-tier provider guide, and Git exercises

**Files:**
- Create: `README.md`
- Create: `sdk_request.py`
- Create: `raw_http.py`
- Create: `failure-matrix.md`
- Modify: `.env.example`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: all working scripts, app routes, tests, and failure matrix from Tasks 1–5.
- Produces: a complete setup and teach-from guide mapped to note sections 1–14.

- [x] **Step 1: Document environment setup and quick-start path**

Include Python/venv/install commands, `.env` copying, active provider configuration, server start command, `/docs`, and browser URL. Explain deleting/restoring `.env` as a controlled classroom exercise.

- [x] **Step 2: Add a provider matrix with key creation links and official quota/model links**

Cover Gemini, Groq, Cerebras, Cohere, Cloudflare Workers AI, NVIDIA NIM, and OpenRouter. State which configuration fields each requires, distinguish free models from free provider-wide quotas, and flag changing eligibility, data terms, and limits.

- [x] **Step 3: Map each lecture section to a demo and explain-along cue**

For sections 1–14 list the command/file to show, the concept to narrate, and one question or observation to elicit from students. Ensure HTTP methods/JSON/status, key safety, SDK/raw HTTP, validation, FastAPI, logging/errors, browser safety, retries, tests, failure matrix, Git, hosted/local, comprehension questions, and practice/homework are covered.

- [x] **Step 4: Document provider switching, troubleshooting, and Git safety commands**

Include missing key, invalid key, model not found, 429/quota, timeout, malformed upstream response, and backend stopped. Include `git check-ignore .env` and `git status` steps, and explain immediate revocation if a real key is committed.

- [x] **Step 5: Document the homework endpoint and mock-test workflow**

Show `/summarize` request example, validation limits, controlled timeout/rate-limit/malformed errors, and the existing tests students can extend.

- [x] **Step 6: Review documentation coverage against sections 1–14**

Check that every lecture heading has a runnable file/route or an explicit student observation task, and remove any instructions requiring a paid key for the default path.
