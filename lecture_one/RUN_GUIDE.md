# Week 1 API Lab: Run and Change Guide

This guide is the class-time runbook for the project. It explains what to install, what to run for each demonstration, where configuration lives, and how to investigate common errors.

## Lecture sequence: follow the notes from Section 1 to 14

Use this order in class. Each entry gives you the lecture point, the file or action to show, what students should notice, and a safe way to demonstrate or fix a failure. Some failures are best simulated by the mocked tests instead of by sending deliberately broken traffic to a live provider.

### Section 1 — What we are building and why

- **Explain:** browser → Python backend → hosted model. The backend is the proxy and the only component allowed to hold the provider key.
- **Open:** `static/index.html`, `static/app.js`, `main.py`, and `providers/` to point out the three programs and the server-side provider call.
- **Show:** start the app using **Run FastAPI application** below, open `/`, submit one prompt, and compare the browser `/chat` request with the Uvicorn log.
- **Ask:** why should the browser never receive a provider key? Show that the browser request contains the student's prompt, while the provider key is read server-side from `.env`.

### Section 2 — HTTP, REST, JSON, and the first request

- **Explain:** method, URL, headers, optional body; then read a request and response as status + headers + body. Cover GET, POST, PUT, PATCH, DELETE, JSON, and the 2xx/4xx/5xx status groups from the notes.
- **Open/run:** `first_request.py`; run `python first_request.py GET` and `python first_request.py POST`. Compare the echoed JSON. This project uses `httpx`; the lecture notes show equivalent introductory code with `requests`.
- **Show:** the project implements runnable GET and POST examples. PUT/PATCH/DELETE are explained as REST methods in the notes, but are not implemented as lab requests. The chat action is POST because it sends data and starts work.
- **Trigger/fix:** if httpbin is unreachable, check internet access; this demo uses a public endpoint. If Python reports a request error or non-success status, inspect the status/output and try again when the connection is available. This script uses a 10-second timeout.
- **Ask:** why does HTTP 200 not prove that the model answer is useful? Students should distinguish transport success from content quality.

### Section 3 — Secrets and configuration

- **Explain:** a key hard-coded in source can be copied from Git, screenshots, or browser code. `.env` is local configuration; `.env.example` documents setting names; `.gitignore` keeps `.env` out of Git.
- **Open:** `.env.example`, `.gitignore`, `settings.py`, and `.env` in the editor. Do not display real key values on a projector or in recordings.
- **Show:** `settings.py` reads settings at startup, validates the selected provider and model, and wraps API keys as `SecretStr`. `.env` holds both Groq and OpenRouter keys; `AI_PROVIDER` selects which one is active.
- **Trigger/fix:** temporarily clear the selected key and run Uvicorn. Startup should fail with a missing setting. Restore the key, confirm `AI_PROVIDER` is `groq` or `openrouter`, and restart. A missing key is fixed in `.env`, not in `main.py`.
- **Security recovery:** if a real key is ever committed or exposed, revoke it at the provider and issue a new key; deleting it from the current file does not remove it from Git history.

### Section 4 — Calling a hosted model: request shape, SDK, raw HTTP

- **Explain:** a chat request has a model and messages; the answer text is nested in the response. SDK and raw HTTP send the same basic request, but the SDK handles more details.
- **Open/run:** with a valid selected key, run `python sdk_request.py`, then `python raw_http.py`. Inspect `settings.py` for provider/model selection; `providers/__init__.py` for compatible base URLs; then compare the two scripts.
- **Show:** `sdk_request.py` uses the OpenAI SDK with a 15-second timeout and SDK retries disabled. `raw_http.py` builds the endpoint, bearer authorization header, JSON body, timeout, and response parsing directly. Neither script prints the key.
- **Trigger/fix:** to show an authentication failure, make a temporary backup of `.env`, replace only the active key with an invalid value, run one script, then restore the valid file. The SDK raises an SDK exception; raw HTTP prints status/body and `raise_for_status()` raises. Fix the key in `.env` and rerun. Do not project or share the raw response if it contains account details.
- **Other errors:** an unknown model or missing model access is fixed by changing the active provider's `*_MODEL` value in `.env`; a timeout or network error needs connection/provider investigation. These direct scripts intentionally do not normalize errors like the FastAPI proxy does.
- **Note:** these comparison scripts support OpenAI-compatible providers (including Groq and OpenRouter). Cohere and Cloudflare use native request formats in the app adapters.

### Section 5 — Pydantic contracts

- **Explain:** request models declare what input is accepted before the app spends a model call.
- **Open:** `schemas.py`, then `/docs` → `POST /chat`.
- **Trigger:** send `{"message":"","temperature":5}` or a temperature above 2. FastAPI returns 422, and no provider request is made. Try a valid message with omitted temperature; it defaults to 0.7.
- **Fix:** use a non-empty message of at most 4,000 characters and a temperature from 0 to 2. If changing these rules for a lesson, edit the `Field(...)` constraints in `schemas.py`; Uvicorn reloads Python changes in development.
- **Show response contract:** `ChatResponse` contains `request_id`, `response`, and `model`.

### Section 6 — FastAPI proxy, async, IDs, and normalized errors

- **Explain:** routes receive validated input, call a provider adapter asynchronously, and return a stable response. Request IDs connect the response to safe logs.
- **Open:** `main.py`, `providers/base.py`, one provider adapter, `retry.py`, and `schemas.py`. Run `python main.py`; show `/docs`, `GET /health`, then `POST /chat`.
- **Show:** the API routes are `GET /health`, `POST /chat`, and the instructor reference `POST /summarize`. The browser page is also served by the app. Logs carry request IDs/event names, not prompts or keys.
- **Error mapping:** invalid caller data → 422; provider timeout → 504; exhausted 429 → 503; other provider failures, network errors, or malformed/empty output → safe 502. The provider's raw internal error is not returned from `/chat`.
- **Fix:** 422 means fix the request. 502 after a real call: check key, permissions, model ID, provider status, and network. 503 means wait for the rate window or switch provider. 504 means investigate latency/network or retry later. Check the terminal by request ID; do not add prompts or keys to logs.
- **Scope note:** the app maps upstream 400/401/403/404/5xx classes to controlled 502 responses. It does not have a dedicated live exercise for every numeric upstream status.

### Section 7 — Browser page and fetch

- **Explain:** idle, loading, success, and error states; same-origin `fetch`; output is untrusted text.
- **Open:** `static/app.js`, `static/index.html`, and browser Developer Tools → Network. Submit a normal prompt and inspect the POST `/chat` body and response.
- **Trigger/fix:** stop Uvicorn with Ctrl+C, submit once, and show the browser network error. Restart the server and try again. For API validation errors, leave the server on and submit invalid input through `/docs`.
- **Security detail:** point to `textContent` in `static/app.js`; model text is rendered as text rather than HTML. The provider key does not appear in browser code or requests.

### Section 8 — Timeouts, rate limits, and retries

- **Explain:** network calls can stall; 429 means slow down; retry only temporary 429/5xx with backoff, jitter, `Retry-After`, and a maximum attempt/time budget. Do not retry 401/other permanent 4xx or timeouts in this design.
- **Open:** `retry.py` and the timeout in the provider adapter (`providers/openai_compatible.py`; the HTTP client timeout is 15 seconds). The retry policy allows up to three attempts and a 45-second total deadline.
- **Demonstrate safely:** run `python -m pytest -q tests/test_retry.py::test_temporary_503_then_success_retries_with_backoff` and `python -m pytest -q tests/test_retry.py::test_repeated_429_stops_after_three_attempts`. The tests replace real waits; no provider quota is used.
- **Show no-retry cases:** `python -m pytest -q tests/test_retry.py::test_permanent_errors_and_timeouts_are_not_retried`.
- **Fix:** if a real provider rate-limits, wait for its quota window or switch provider in `.env` and restart. If timeout persists, check connectivity/provider latency; do not blindly add retries because the upstream may have completed and billed the request.
- **Difference from notes:** the notes discuss separate connect/read/write/pool timeout examples and a 45-second retry budget. This implementation uses a 15-second HTTP client timeout per attempt plus the 45-second overall retry deadline; teach the code's actual values when inspecting the implementation.

### Section 9 — Automated tests and failure matrix

- **Explain:** arrange/act/assert; mocks are repeatable, fast, free, and can force a failure that a live provider may not produce on demand.
- **Open/run:** `tests/test_api.py`, `tests/test_providers.py`, `tests/test_retry.py`, and `tests/conftest.py`. Full suite: `python -m pytest -q`.
- **Targeted examples:**
  - `python -m pytest -q tests/test_api.py::test_empty_message_is_rejected_before_provider_is_called`
  - `python -m pytest -q tests/test_api.py::test_provider_401_becomes_safe_502_without_provider_details`
  - `python -m pytest -q tests/test_api.py::test_provider_timeout_returns_safe_504_with_request_id`
  - `python -m pytest -q tests/test_api.py::test_malformed_provider_response_becomes_safe_502`
  - Retry examples are in Section 8 above.
- **Show:** open `failure-matrix.md` and record Expected vs Observed. The test fixtures use dummy credentials; tests never call the real provider.
- **Fix:** a failing assertion means actual behavior differs from the intended contract. Read the test's arrange/act/assert steps, then inspect the related route (`main.py`), schema (`schemas.py`), adapter (`providers/`), or retry code (`retry.py`). Do not “fix” a failed mock exercise by changing a real API key.

### Section 10 — Git and publishing

- **Explain:** Git history preserves past versions, including a committed secret.
- **Open/run:** `.gitignore`; when using Git, run `git check-ignore -v .env` and confirm `.env` is absent from the staged file list. This working folder may not yet be initialized as a Git repository; if starting one, use `git init` first.
- **Fix:** if `.env` appears as trackable, stop before committing and check `.gitignore`. If it was already committed, revoke/rotate the key; a later deletion is not enough.

### Section 11 — Hosted API or local model

- **Teach as discussion:** compare setup time, internet/provider dependency, privacy, hardware, operations, scaling, and offline use. No command is required; the supported lab calls are hosted providers.
- **Prompt:** what operational work would the team take on if it ran a model locally?

### Section 12 — Ten takeaways

- **Review:** browser-to-backend proxy; secrets outside code; status and response content; SDK vs raw HTTP; Pydantic validation; timeouts; bounded retries; request IDs without prompts/secrets; mocked tests.
- **Use:** the matching ten-point recap in the lecture notes. Ask students to point to the file that demonstrates each claim.

### Section 13 — Check understanding

- **Run:** no code required. Use the ten questions in the notes as a quick oral review.
- **If students get stuck:** point them to `schemas.py` for 422, `main.py` for normalized 502/503/504, `retry.py` for retries, `static/app.js` for `textContent`, and `tests/` for mocked cases.

### Section 14 — Practice tasks and homework

- **Practice:** rerun first_request GET/POST; show missing-key startup validation; compare SDK/raw HTTP; test invalid input in `/docs`; inspect browser Network; stop the backend; run mocked success/timeout/401/429/malformed/retry cases; fill `failure-matrix.md`; verify `.env` is ignored before sharing.
- **Homework route:** `POST /summarize` is already implemented in `main.py` and its contracts are in `schemas.py` as the instructor reference. For an assignment, provide students a starter copy with that route and its two schemas removed. Ask them to add validation, structured output, normalized failures, and at least five mocked tests.
- **Run summary demo:** use `/docs` → `POST /summarize`, or the curl example under **API routes and sample requests** below. The route accepts 1–12,000 characters. Discuss chunking/background jobs for much larger documents.

## Quick reference: project map

| File or folder | What it is for | When to open or run it |
|---|---|---|
| `.env` | Your private local provider settings and API keys | Edit to choose Groq/OpenRouter and set keys. Never share or commit it. |
| `.env.example` | Safe template showing available setting names | Copy it to create a fresh `.env`. Keep this file free of real keys. |
| `first_request.py` | A small GET/POST JSON request to the public httpbin echo service | Run for the first HTTP request lesson; it does not use an AI key. |
| `sdk_request.py` | One model request using the OpenAI Python SDK | Run to show how an SDK hides some HTTP details. |
| `raw_http.py` | The same style of model request using `httpx` directly | Run to inspect URL, headers, body, status, and raw response. |
| `settings.py` | Reads and validates `.env` settings | Open when explaining configuration and startup checks. |
| `providers/` | Makes requests to each provider and parses its response | Open when comparing provider adapters and response formats. |
| `schemas.py` | Validates API request fields and defines response shapes | Open when showing Pydantic input rules. |
| `main.py` | FastAPI server, routes, provider calls, error handling, and request IDs | Run the web application and show the backend flow. |
| `static/` | Browser page, JavaScript, and CSS | Open `app.js` while showing the browser's POST request. |
| `retry.py` | Bounded retry and backoff logic | Open during the rate-limit and retry lesson. |
| `tests/` | Mocked examples of expected success and failures | Run to demonstrate errors without spending provider quota. |
| `failure-matrix.md` | Worksheet for recording observed failures and responses | Fill in with the class. |

## Prepare the Python environment

Use Python 3.11 or newer. Open a terminal in this project folder.

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks environment activation, use Command Prompt instead:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

After activation, the terminal prompt usually shows `(.venv)`. Run the remaining commands in that same terminal. If you close it, activate the environment again next time.

## Configure Groq and OpenRouter

The project `.env` already has configuration slots for Groq and OpenRouter. Open it in your editor and put each key after its matching equals sign. Keep the value on one line, with no quotes or spaces around it.

```dotenv
AI_PROVIDER=groq
GROQ_API_KEY=paste_your_groq_key_here
GROQ_MODEL=openai/gpt-oss-20b

OPENROUTER_API_KEY=paste_your_openrouter_key_here
OPENROUTER_MODEL=openrouter/free
```

Replace the example text with the real keys locally. Do not send keys in chat, put them in Python files or browser JavaScript, or show them in a screen recording. `.env` is ignored by Git; `.env.example` is the shareable template.

`AI_PROVIDER` selects which key and model the application uses. Only the selected provider's key is needed to start the app. Since both keys are configured, change this setting to switch providers:

```dotenv
AI_PROVIDER=groq
```

or:

```dotenv
AI_PROVIDER=openrouter
```

Save `.env` and restart the server after changing provider or model. Settings are loaded when Python starts. Model IDs and availability can change; if a request reports an unknown model or no access, check the provider dashboard and update the matching `*_MODEL` line.

Other supported providers and their variable names are listed in `.env.example`. Cloudflare also requires `CLOUDFLARE_ACCOUNT_ID`.

## Standalone HTTP demo

These commands call httpbin, which echoes the request as JSON. They need internet access but no AI provider key.

```bash
python first_request.py GET
python first_request.py POST
```

The GET example sends no JSON body. The POST example sends a JSON `message`. The script prints the HTTP status and parsed JSON response. The default is POST if you run `python first_request.py` without an argument.

This script only supports GET and POST. The web application also uses GET and POST. PUT, PATCH, and DELETE are not runnable examples in this lab.

## Standalone model-call demos

First ensure `.env` contains a working selected key. Groq and OpenRouter work with these two examples.

```bash
python sdk_request.py
python raw_http.py
```

The SDK example lets the library build the request and parse the response. The raw HTTP example shows the request ingredients directly and prints the response status and raw body. Both use a 15-second timeout and do not automatically retry.

The SDK/raw examples support OpenAI-compatible providers: Gemini, Groq, Cerebras, NVIDIA, and OpenRouter. Cohere and Cloudflare use native formats in the app adapters, so these two comparison scripts reject them.

## Run the FastAPI application

Make sure the selected provider key is filled in before starting. The app validates settings during startup, so it will stop early if the selected key is missing.

```bash
python main.py
```

This runs Uvicorn from the bottom of `main.py`, bound to `127.0.0.1` on port `8000`. Reload is enabled, so Uvicorn restarts the local development server when Python files change. Leave this terminal running while you use the app. The equivalent explicit command is `python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`.

Open these local URLs:

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/` | Browser chat page for the class |
| `http://127.0.0.1:8000/docs` | Interactive API documentation; send requests to endpoints |
| `http://127.0.0.1:8000/health` | Health check; should return `{"status":"healthy"}` |

Stop the server with `Ctrl+C` in its terminal.

## API routes and sample requests

### `GET /health`

Checks that the app is responding. This route does not call the AI provider.

```bash
curl http://127.0.0.1:8000/health
```

### `POST /chat`

Use `/docs` or send JSON from a terminal:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain an API in one sentence","temperature":0.7}'
```

`message` must be 1–4,000 characters. `temperature` is optional and must be between 0 and 2. The response contains a `request_id`, the model's `response`, and the model ID.

### `POST /summarize`

This instructor reference route accepts text from 1 to 12,000 characters:

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"APIs let programs exchange requests and responses. A backend can validate input and protect provider keys."}'
```

The response contains a `request_id`, `summary`, and model ID. For a live class, `/docs` is often easiest because it builds the request form for you.

## Browser-to-provider flow

1. Start Uvicorn and open `/`.
2. Send a prompt in the page.
3. Open browser Developer Tools, then select **Network**.
4. Select the `/chat` request and inspect its JSON body and response.
5. Compare it with the Uvicorn terminal logs and the provider adapter in `providers/`.

The browser sends a request only to this backend. Python reads the secret key from `.env` and makes the provider request. The browser never receives the provider key. Server logs include request IDs and event names, not the prompt or key.

## Error demonstrations and fixes

Try these in `/docs` or use the mocked tests below:

| Demonstration | How to trigger | Expected result |
|---|---|---|
| Invalid chat input | Empty `message`, or `temperature` above 2 | HTTP 422; provider is not called |
| Missing selected key | Clear the selected key in `.env`, then start Uvicorn | Startup validation error |
| Invalid provider key | Temporarily replace the selected key with an invalid value and call `/chat` | Safe HTTP 502 response; restore the real key afterward |
| Provider rate limit | Use the mocked tests; do not intentionally exhaust a real quota | Retry is bounded; final API response is HTTP 503 |
| Provider timeout | Use the mocked tests | HTTP 504 |
| Invalid or empty provider response | Use the mocked tests | HTTP 502 |
| Backend unavailable | Stop Uvicorn and submit from the browser | Browser connection/network error; no API JSON response |

Validation errors from FastAPI are 422. Provider timeouts map to 504. Rate limits (429) and retry exhaustion map to 503. Other provider failures, network errors, and malformed responses map to safe 502 responses. The API does not expose the provider's raw credential or internal error text to the browser.

Avoid repeated real requests with a deliberately bad key: the mock tests are safer and deterministic.

## Run the mocked tests

From the activated virtual environment:

```bash
python -m pytest -q
```

The tests use fake providers and HTTP mock transports. They do not contact Groq, OpenRouter, or another live AI provider, spend quota, or wait through real retry delays. Look especially at `tests/test_api.py`, `tests/test_providers.py`, and `tests/test_retry.py` when teaching success, validation, timeouts, authentication failures, rate limits, malformed responses, and retry-then-success.

## Where to change settings and code

| Change you want | Edit here |
|---|---|
| Choose Groq/OpenRouter or another supported provider | `.env` → `AI_PROVIDER` |
| Add or replace a local provider key | `.env` → matching `*_API_KEY` or `CLOUDFLARE_API_TOKEN` |
| Change a model | `.env` → matching `*_MODEL` |
| Change accepted chat/summarize input or response fields | `schemas.py` |
| Change API routes, response mapping, request IDs, or logging | `main.py` |
| Change the browser UI behavior | `static/app.js` |
| Change visual styles | `static/styles.css` |
| Change provider URL, headers, body, or response parsing | matching file in `providers/` |
| Change retry policy or backoff | `retry.py` |
| Change SDK demo | `sdk_request.py` |
| Change raw HTTP demo | `raw_http.py` |
| Change introductory GET/POST demo | `first_request.py` |

After editing `.env`, restart the app. After editing Python code while running with `--reload`, Uvicorn normally reloads automatically. If an import or configuration error appears, stop the server, read the terminal traceback, fix the setting or code, then start it again.

## Common troubleshooting

| Symptom | Check |
|---|---|
| `python` command not found | Activate `.venv`; on macOS/Linux create it with `python3`. On Windows use `py` to create it. |
| `ModuleNotFoundError` | Confirm `.venv` is active and run `python -m pip install -r requirements.txt`. |
| Uvicorn says a required key is missing | Check `AI_PROVIDER` spelling and fill the matching key in `.env`. Restart Uvicorn. |
| Provider returns 401/403 | Check that the key is for the selected provider, is active, and has model access. Do not print or share it while debugging. |
| Provider reports model not found or unavailable | Check the provider's current model ID and update its matching `*_MODEL`. |
| Provider returns rate limit/quota error | Wait for the provider's quota window or switch provider in `.env`; restart Uvicorn. |
| Browser cannot connect | Confirm Uvicorn is still running and use `127.0.0.1:8000`. |
| httpbin request fails | Check internet connectivity; this introductory script uses a public endpoint. |

## Before sharing the project

- Keep actual keys in `.env` only.
- Keep `.env.example` empty of real credentials.
- Check that `.env` is ignored by Git before staging files.
- If a real key is ever committed or shown publicly, revoke it in the provider dashboard and create a replacement.

For a longer lecture outline and provider references, see [README.md](README.md).
