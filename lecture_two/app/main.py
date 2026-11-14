from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from groq import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

from app.evidence import evidence_report
from app.config import ROOT
from app.lab import router as lab_router
from app.groq_service import ExtractionFailure, GroqExtractionService
from app.schemas import ExtractionRequest, ExtractionResponse

app = FastAPI(
    title="Week 2 — Structured Extraction",
    description="Extract contact fields with Groq. Schema validity is not factual correctness.",
)
app.include_router(lab_router)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def classroom():
    return FileResponse(ROOT / "static" / "index.html")


@app.middleware("http")
async def request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def get_service():
    # Return a factory, so SDK setup happens inside the route's error handling,
    # after FastAPI has validated the input. Tests replace this with a fake.
    return GroqExtractionService


@app.get("/health")
def health():
    """Local liveness only; this does not call or check Groq."""
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractionResponse)
def extract(req: ExtractionRequest, request: Request, factory=Depends(get_service)):
    service = None
    try:
        service = factory(prompt_version=req.prompt_version)
        if req.repair:
            data, repaired = service.extract_with_repair(req.text, req.mode)
        else:
            data, repaired = service.extract(req.text, req.mode), False
        return ExtractionResponse(
            request_id=request.state.request_id,
            prompt_version="contact-extraction-" + req.prompt_version,
            model=service.model_for(req.mode), mode=req.mode,
            schema_valid=True, repaired=repaired, provider_calls=service.call_count,
            evidence=evidence_report(data.model_dump(), req.text), data=data,
        )
    except ValueError:
        status, message = 503, "Configure GROQ_API_KEY on the backend."
    except APITimeoutError:
        status, message = 504, "Groq timed out; this request was not retried."
    except RateLimitError:
        status, message = 503, "Groq rate limit reached; try again later."
    except (APIConnectionError, APIStatusError):
        status, message = 502, "Groq request failed; check server configuration or availability."
    except ExtractionFailure:
        status, message = 502, "Unable to produce a complete, schema-valid extraction."
    finally:
        if isinstance(service, GroqExtractionService):
            service.client.close()
    raise HTTPException(status_code=status, detail={
        "error": message, "request_id": request.state.request_id,
    })
