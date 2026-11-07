"""FastAPI proxy that keeps provider credentials on the server."""

from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path
from collections.abc import Awaitable, Callable
from uuid import uuid4

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response

from providers import get_provider
from providers.base import Provider, ProviderError
from retry import call_with_retry
from schemas import ChatRequest, ChatResponse, SummarizeRequest, SummarizeResponse
from settings import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("week1_api")
STATIC_DIR = Path(__file__).parent / "static"
PAGE_HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
APP_JS = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
APP_CSS = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")


def create_app(
    settings: Settings,
    provider: Provider | None = None,
    *,
    retry_sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    jitter_source: Callable[[], float] = random.random,
) -> FastAPI:
    app = FastAPI(title="Week 1 AI Model Proxy")
    active_provider = provider or get_provider(settings)

    async def complete_with_safe_errors(
        message: str, temperature: float, request_id: str
    ) -> str | JSONResponse:
        try:
            answer = await call_with_retry(
                lambda: active_provider.complete(message, temperature),
                sleep=retry_sleep,
                jitter_source=jitter_source,
            )
        except (httpx.TimeoutException, TimeoutError):
            logger.warning("request_id=%s event=provider_timeout", request_id)
            return JSONResponse(
                status_code=504,
                content={
                    "request_id": request_id,
                    "detail": {"error": "AI provider timeout", "request_id": request_id},
                },
            )
        except ProviderError as error:
            logger.warning(
                "request_id=%s event=provider_error status=%s",
                request_id,
                error.status_code,
            )
            if error.status_code == 429:
                status_code, message = 503, "AI provider rate limit exceeded"
            elif error.status_code == 502:
                status_code, message = 502, "Unable to process AI provider response"
            else:
                status_code, message = 502, "AI provider request failed"
            return JSONResponse(
                status_code=status_code,
                content={
                    "request_id": request_id,
                    "detail": {"error": message, "request_id": request_id},
                },
            )

        if not isinstance(answer, str) or not answer.strip():
            logger.warning("request_id=%s event=provider_empty_response", request_id)
            return JSONResponse(
                status_code=502,
                content={
                    "request_id": request_id,
                    "detail": {
                        "error": "Unable to process AI provider response",
                        "request_id": request_id,
                    },
                },
            )
        return answer.strip()

    @app.get("/", include_in_schema=False, response_class=HTMLResponse)
    async def home() -> HTMLResponse:
        return HTMLResponse(PAGE_HTML)

    @app.get("/static/app.js", include_in_schema=False)
    async def browser_javascript() -> Response:
        return Response(APP_JS, media_type="text/javascript")

    @app.get("/static/styles.css", include_in_schema=False)
    async def browser_styles() -> Response:
        return Response(APP_CSS, media_type="text/css")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse | JSONResponse:
        request_id = str(uuid4())
        logger.info("request_id=%s event=chat_started", request_id)
        result = await complete_with_safe_errors(
            request.message, request.temperature, request_id
        )
        if isinstance(result, JSONResponse):
            return result
        logger.info("request_id=%s event=chat_completed", request_id)
        return ChatResponse(
            request_id=request_id,
            response=result,
            model=active_provider.model,
        )

    @app.post("/summarize", response_model=SummarizeResponse)
    async def summarize(request: SummarizeRequest) -> SummarizeResponse | JSONResponse:
        request_id = str(uuid4())
        logger.info("request_id=%s event=summarize_started", request_id)
        prompt = (
            "Summarize the following text in clear, concise language. "
            "Preserve its main points and do not add facts.\n\n"
            f"Text:\n{request.text}"
        )
        result = await complete_with_safe_errors(prompt, 0.3, request_id)
        if isinstance(result, JSONResponse):
            return result
        logger.info("request_id=%s event=summarize_completed", request_id)
        return SummarizeResponse(
            request_id=request_id,
            summary=result,
            model=active_provider.model,
        )

    return app


app = create_app(Settings())


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
