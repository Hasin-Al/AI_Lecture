# Week 1 API-First Python Lab Design

## Intent

Turn the Week 1 lecture notes into a classroom-ready, runnable Python project. Students should be able to follow the lecture in order, observe HTTP requests and failures, and end with a browser calling a FastAPI proxy that talks to a hosted AI model.

## Goals

- Provide hands-on examples for the topics and practice tasks in sections 1–14 of the supplied notes.
- Keep provider API keys in `.env`, provide `.env.example`, and ensure `.env` is ignored by Git.
- Demonstrate Python HTTP/JSON, settings, SDK and raw HTTP calls, Pydantic validation, FastAPI, browser `fetch`, request IDs/logging, normalized errors, timeouts/retries, mocked tests, Git safety, and the `/summarize` homework extension.
- Let the instructor choose an active provider through configuration. Include free API paths verified in official documentation on 2026-11-06: Google Gemini API, Groq, Cerebras Inference, Cohere trial API, Cloudflare Workers AI, NVIDIA NIM hosted endpoints for prototyping, and OpenRouter free models. Preserve provider-specific API differences behind small adapters and show their setup and current model selection in the guide.
- Mark free quotas, model IDs, regional/account eligibility, and terms as subject to change; students must verify their account limits before class. Do not treat one-off promotional credits as recurring free tiers.
- Keep the default demo short, safe, and low-volume. Never expose keys in browser code, logs, or responses.

## Non-goals

- Exhaustively catalog every free or promotional AI API worldwide. “Free tier providers” is an open-ended and changing set; initial support is the six officially documented providers listed above, with a simple provider interface for adding more.
- Promise that any provider or model is available in every country/account or is suitable for production.
- Build authentication, persistent conversation history, deployment infrastructure, or a polished frontend framework application.
- Call paid providers by default or make a real provider call in automated tests.

## Constraints

- Python project, FastAPI backend, plain HTML/CSS/JavaScript frontend, Pydantic request/response models.
- Use `.env` for local secrets and environment variables in hosted environments.
- Network calls require explicit timeouts. Provider retries must be limited to transient 429/5xx failures, honor `Retry-After` when valid, use exponential backoff with jitter, and have a total time budget. Timeouts and non-transient 4xx failures are not retried.
- Automated tests use mocked provider HTTP calls; tests must not spend credits or wait through real backoff sleeps.
- Render model text with `textContent`; do not inject model output as HTML.
- Honor the repository workflow: save design and implementation plan under `docs/superpowers/`, and do not start implementation before design approval.

## Approaches

1. **One evolving project (selected by the instructor’s “do what will be the best” direction):** build one repo in lecture order, using small demonstrations that culminate in the full proxy/browser flow. This provides continuity and reuses the same contracts and settings. Provider adapters keep the main path readable while still showing differences.
2. **Separate standalone scripts for every topic:** isolates each concept but repeats configuration and makes the final end-to-end system harder to connect to earlier examples.

The first approach is selected because the lecture itself builds one system in sequence and the class goal is a live working demonstration.

## Proposed architecture

- `README.md`: prerequisites, virtual environment and install commands, `.env` setup, provider key/model table with official links, lesson-by-lesson runbook mapped to note sections, expected outputs, instructor prompts, common failures, practice/homework, and Git secret checks.
- `first_request.py`: public echo-server POST and GET exercise with a timeout.
- `settings.py`: validated Pydantic settings loaded from `.env`; selected provider and provider credentials/model names are explicit.
- `providers/`: a small provider interface and adapters. OpenAI-compatible calls are used for providers that document this compatibility; dedicated request/response adapters cover Cohere and Cloudflare where their wire formats differ. Provider names, base URLs, required `.env` variable names, and model IDs are documented and configurable rather than hardcoded as secrets.
- `schemas.py`: `ChatRequest`, `ChatResponse`, and `SummarizeRequest` contracts matching lecture constraints.
- `main.py`: FastAPI health and chat routes, request IDs and safe structured logs, normalized provider errors, bounded async HTTP requests, retry policy, `/docs`, and static browser page serving. The browser never receives a provider key.
- `static/`: small browser UI showing idle/loading/success/error and request IDs, with safe `textContent` rendering.
- `tests/`: deterministic API tests for health, invalid input/no upstream call, success, timeout, 401, 429 exhaustion, 5xx, malformed/empty response, retry-then-success, and summary behavior. Mock provider calls and replace sleep in retries.
- `failure-matrix.md`: blank student observation table matching the notes.
- `.env.example`, `.gitignore`, and pinned/minimum dependency declarations.

## Provider scope and teaching notes

The supported free access set is an initial documented snapshot, not a promise of permanent terms. The README will link official sources and state that students should check current account quotas, model availability, eligibility, data use, and whether a payment method is required. Official pages checked for this design: [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), [Groq rate limits](https://console.groq.com/docs/rate-limits), [Cerebras pricing](https://inference-docs.cerebras.ai/support/pricing), [Cohere trial key limits](https://docs.cohere.com/v2/docs/rate-limits), [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/), [NVIDIA NIM development access](https://docs.api.nvidia.com/nim/docs/run-anywhere), and [OpenRouter free models](https://openrouter.ai/collections/free-models/). OpenRouter free models have model-specific availability and rate limits; the README will avoid baking a transient catalog model into code where possible, while giving a current example students can replace. OpenAI remains available as a comparison in the notes but is not required for the no-cost hands-on path.

## Acceptance criteria

- An instructor can follow the README from setup through the final practice tasks without needing undocumented setup.
- Every note section has a concrete demo, explain-along prompt, or student exercise in the runbook.
- `.env.example` contains no real secrets; `.env` is ignored by Git.
- The full proxy works with at least one configured provider and provider switching is supported by the documented adapters.
- Invalid requests are rejected before provider calls; provider errors return a safe message and request ID.
- Tests cover the failure matrix without external API calls, and the browser handles backend network failure safely.
- The summary homework route validates input, calls the configured provider through the backend, and has mocked tests.

## Builder calls

- Default the runbook to a single active provider selected in `.env`; students only need one account/key to complete the core lecture, while the others are optional provider-comparison exercises.
- Use `httpx.AsyncClient` in the FastAPI path so the lecture’s `async` explanation corresponds to non-blocking network I/O.
- Keep real provider credentials out of automated test settings by setting dummy values before importing the app.
