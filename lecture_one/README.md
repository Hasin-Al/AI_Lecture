# Week 1 Lab: API-First Python and AI Service Foundations

This folder turns the lecture notes into one project that grows from a first HTTP request into a small AI application. Use it as a live teaching script: run one step, inspect the request or response, then ask students what they notice.

The finished flow is:

```text
Browser page  -- POST /chat -->  FastAPI + Pydantic  -- HTTPS -->  selected AI provider
     ^                                |                                  |
     +------- safe JSON + request ID --+<---------------------------------+
```

The browser never receives an AI provider key. The key is read by Python from `.env` on the server side.

## 1. Setup

Use Python 3.11 or newer. From this folder:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env`, choose one provider, and fill only its key. For example:

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=put_your_key_here
```

Keep the real key only in `.env`. Do not paste it into Python, browser JavaScript, a screenshot, a chat, or a Git commit. `.env.example` documents variable names and safe model defaults; it must not contain a real key. The application validates the selected provider's key at startup, so a missing key fails early with a settings error.

## 2. Free API provider options

These are the seven provider paths supported in this lab, with no-cost API access documented by the providers when this guide was prepared on **November 6, 2026**. This is a lab selection, not a complete directory of every free AI API. They are examples for learning, not a promise that a model, quota, region, signup path, or free offer will stay the same. Before class, check the official page and your provider dashboard. Quotas can vary by account, model, and region; some free tiers can involve data-use terms or require a payment method. Use classroom prompts only—do not submit private customer, student, or personal data.

| Provider | Free access documented | `.env` fields | Official setup and limits |
|---|---|---|---|
| Google Gemini API | Free token tier for selected models; free-tier content may be used to improve Google products | `GEMINI_API_KEY`, `GEMINI_MODEL` | [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), [OpenAI-compatible API](https://ai.google.dev/gemini-api/docs/openai), [create a key](https://aistudio.google.com/app/apikey) |
| Groq | Free developer access with per-model rate limits | `GROQ_API_KEY`, `GROQ_MODEL` | [rate limits](https://console.groq.com/docs/rate-limits), [chat API](https://console.groq.com/docs/api-reference), [create a key](https://console.groq.com/keys) |
| Cerebras Inference | Free API tier with lower rate limits | `CEREBRAS_API_KEY`, `CEREBRAS_MODEL` | [pricing and free tier](https://inference-docs.cerebras.ai/support/pricing), [create a key](https://cloud.cerebras.ai/) |
| Cohere | Free, rate-limited trial key; trial usage has a monthly call limit | `COHERE_API_KEY`, `COHERE_MODEL` | [trial limits](https://docs.cohere.com/v2/docs/rate-limits), [Chat API](https://docs.cohere.com/v2/reference/chat), [create a key](https://dashboard.cohere.com/api-keys) |
| Cloudflare Workers AI | Free allocation of 10,000 Neurons per day; not every model is available on the free plan | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_MODEL` | [pricing and free allocation](https://developers.cloudflare.com/workers-ai/platform/pricing/), [model catalog](https://developers.cloudflare.com/workers-ai/models/), [free-model examples](https://developers.cloudflare.com/changelog/post/2026-07-28-models-require-workers-paid/) |
| NVIDIA NIM hosted APIs | NVIDIA Developer Program provides free access for prototyping, research, development, and testing; production has separate licensing | `NVIDIA_API_KEY`, `NVIDIA_MODEL` | [NIM development access](https://docs.api.nvidia.com/nim/docs/run-anywhere), [API Catalog quickstart](https://docs.api.nvidia.com/nim/docs/api-quickstart), [API catalog](https://build.nvidia.com/explore/discover) |
| OpenRouter | Free models are available with rate limits; free model IDs can change | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | [free models and limits](https://openrouter.ai/collections/free-models/), [create a key](https://openrouter.ai/settings/keys) |

The default model IDs in `.env.example` are a starting point, not permanent IDs. OpenRouter's `openrouter/free` dynamic route can select an eligible free model; a specific model can be used by setting its current `:free` ID instead. Cloudflare's model catalog marks which models need a paid plan. NVIDIA's free hosted endpoints are for development and testing, not a production service. Cohere's trial key has a monthly usage cap. Check your account before class and keep prompts short to conserve quota.

The provider registry uses one OpenAI-compatible HTTP format for Gemini, Groq, Cerebras, NVIDIA, and OpenRouter. Cohere and Cloudflare use their own request and response shapes. All seven are selectable with `AI_PROVIDER`; the actual active key remains server-side.

## 3. Start the app

From the activated virtual environment:

```bash
python main.py
```

This starts Uvicorn on `127.0.0.1:8000` with reload enabled. The equivalent explicit command is `python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`.

Open these URLs:

- Browser demo: <http://127.0.0.1:8000/>
- Interactive API docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

For the first request, use a short harmless prompt. Open browser DevTools → **Network**, submit it, and inspect `POST /chat`. Students should see the message and temperature in the request body, but no provider key. Stop the server with `Ctrl+C` when the class reaches the backend-offline exercise.

## 4. Lesson-by-lesson teaching runbook

### Sections 1–2: system flow, HTTP, REST, JSON, and status codes

Run the echo server example without needing a model key:

```bash
python first_request.py POST
python first_request.py GET
```

Ask students to find the method, URL, JSON body, status, and response in the printed result. POST sends a JSON message to httpbin's `/post`; GET calls `/get` without a body. Change the method and compare the echo result. Both requests set a ten-second timeout.

Use `/docs` to try `GET /health` and `POST /chat`. Mention that a 200 means the HTTP request succeeded, while application code still checks that the provider returned usable text. The Pydantic validation example later gives the 422 case.

**Ask:** What should a browser send, and what should stay between our backend and the model provider?

### Section 3: secrets and configuration

Show `.env.example`, then `.env`, `settings.py`, and `.gitignore`. Point out that `Settings()` validates the selected key when the app starts. To demonstrate the missing-key error safely, rename `.env` to `.env.saved`, restart the app, read the field name in the validation error, stop the server, and restore `.env`. Do not print the real key in the terminal or projector.

**Ask:** If a key reaches Git history, why is deleting it in the next commit not enough? Answer: revoke the old key at the provider and issue a new one; the old value remains in Git history.

### Section 4: hosted model calls with SDK and raw HTTP

With a compatible provider selected and its `.env` key set, run:

```bash
python sdk_request.py
python raw_http.py
```

Both use the same model and message. In `sdk_request.py`, show how the SDK handles the HTTP details and provides a parsed response object. In `raw_http.py`, inspect the URL, `Authorization: Bearer ...` header, JSON request body, HTTP status, raw response, and parsed assistant text. The key is read by Python, never printed. These comparison scripts use the OpenAI-compatible interface; the app's Cohere and Cloudflare adapters show native formats.

The SDK is configured with a 15-second timeout and `max_retries=0` so a provider failure is visible rather than silently repeated.

**Ask:** What changed between the two scripts, and which one would you use to debug an unexpected status or response shape?

### Section 5: Pydantic contracts

Show `schemas.py`, then try `/chat` in `/docs` with:

```json
{"message": "", "temperature": 5}
```

Expect HTTP 422. Confirm that the provider was never called. `message` must contain 1–4,000 characters, and `temperature` must be between 0 and 2. This check happens before model usage.

### Section 6: FastAPI proxy

Show `/health`, `/chat`, and the request/response models in `main.py`. Run the app with `uvicorn`; open `/docs` and send one valid request. Explain that `main:app` means the `app` object in `main.py`, and that `async` endpoints await network calls so the server can handle other work while a provider responds.

### Section 7: logs and browser page

Open the browser page and Network panel. Point out the four states: ready, waiting, answer received, and error. Compare the browser's `/chat` request with the backend's outgoing provider request. The browser calls the same-origin backend only; the server log uses the request ID and event name, not the user's prompt or credential. `static/app.js` writes model output with `textContent`, so a string such as `<script>alert(1)</script>` is displayed as text.

### Section 8: timeouts, rate limits, retries, and failure causes

Show the explicit 15-second provider timeout and the 45-second total retry budget. In `retry.py`, trace the schedule: 2, 4, then 8 seconds (with jitter added), at most three attempts; a numeric `Retry-After` header is honored up to the cap. The third failed request stops without a fourth attempt. Timeouts, invalid credentials, other 4xx errors, and malformed responses are not retried. A timeout is ambiguous: the provider might have finished and billed the request after our client stopped waiting.

Use the mocked tests rather than deliberately exhausting a real provider quota. Tests replace waiting with a no-op and can produce a 429 or 503 on demand.

**Ask:** Why can the model be online while the API call fails? Examples: invalid/expired key, missing model access, wrong model ID, bad request, quota/rate limit, DNS/TLS/network issue, provider overload, timeout, malformed response, or a bug in our backend.

### Section 9: automated tests

Run the tests from the activated virtual environment:

```bash
python -m pytest -q
```

Explain arrange/act/assert in `tests/test_api.py`. The tests use fake providers and `httpx.MockTransport`; they do not contact a live AI provider, consume quota, or wait through backoff. Start with health and invalid input, then show success, provider timeout, 401, rate-limit exhaustion, malformed response, and retry-then-success.

### Section 10: Git and secret safety

This folder is intentionally not initialized as a Git repository; use the lecture steps to create one:

```bash
git init
git check-ignore -v .env
git add .
git status --short
```

Confirm `.env` does not appear in the staged list and `.env.example` does. If a real key is ever committed, revoke it immediately—even after deleting the file from the latest version.

### Section 11: hosted API or local model

| Hosted provider | Local model |
|---|---|
| Fast to start; provider runs the hardware | Requires model downloads, hardware, and setup |
| Calls use a network and provider account | Can work offline after setup |
| Provider handles scaling | You handle scaling, memory, and operations |
| Prompt data goes to the provider under its terms | Data can stay on your own machine |
| Good first product path when privacy and offline needs allow it | Useful when privacy, offline access, customization, or predictable volume justifies operations |

### Section 12: ten takeaways

Recap the ten points from the notes: backend proxy; secrets outside code; HTTP request/response and status; check answer content; SDK versus raw HTTP; Pydantic rejects bad input; always use timeouts; bounded retries; request IDs without secrets/prompts; mock providers for tests.

### Section 13: quick oral review and answer key

1. **Why can't a provider key live in browser JavaScript?** Anyone using the page can inspect and copy it.
2. **What happens to an empty message and temperature 5?** 422 before the provider call.
3. **Retry a 401?** No. The key or permission must be fixed; another identical request cannot fix it.
4. **422 vs 502?** 422 means our API rejected the caller's input; 502 means an upstream provider response could not be processed or succeeded.
5. **Why can a timeout cost money?** The provider may finish after the client stops waiting.
6. **What does jitter do?** It spreads client retries so they do not all arrive at once.
7. **How test 429 without credits?** Mock the provider response and assert the API's controlled result.
8. **Four causes despite an available model?** Bad key, wrong model permission/name, quota, malformed request, network/DNS/TLS, timeout, provider overload, bad response parsing, or our own bug.
9. **When raw HTTP?** When debugging exact headers/body/status, using a provider without a compatible SDK, or using an unsupported SDK feature.
10. **Why `textContent`?** It displays model output as text rather than executing markup or scripts.

### Section 14: in-class practice and homework

- Run `first_request.py` with POST and GET; describe what changed.
- Rename `.env`, start the app to see startup validation, then restore the file.
- Run `sdk_request.py` and `raw_http.py`; set a deliberately invalid key temporarily and compare the status/error. Restore the good key without showing it to the class.
- Use `/docs` to submit an empty message and temperature 5.
- Inspect the browser request in DevTools. Stop the backend and submit once more.
- Run the mocked tests for success, timeout, 401, repeated 429, malformed response, and retry-then-success.
- Fill in [the failure matrix](failure-matrix.md) with what the class observed.
- Before pushing to a remote Git host, check `git status` and verify `.env` is ignored.

**Homework:** The repository includes an instructor reference implementation of `POST /summarize` in `main.py` and `schemas.py`. To assign the build, give students a starter copy with that route and its two schemas omitted. Ask them to accept non-empty text up to 12,000 characters, call the configured model through the backend, return a structured summary, normalize timeout/rate-limit/malformed-response errors, and write at least five mocked tests. A sample request is:

```bash
curl -X POST http://127.0.0.1:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"APIs let programs exchange requests and responses. A backend can validate input and protect provider keys."}'
```

The response includes `request_id`, `summary`, and `model`. For very large documents, explain why chunking or a background job is safer than one long synchronous request.

## 5. Useful commands

```bash
python first_request.py POST
python first_request.py GET
python sdk_request.py
python raw_http.py
python main.py
python -m pytest -q
```

Use `python -m pytest`, not the `pytest` console shortcut, so the project root stays importable in this teaching setup.
