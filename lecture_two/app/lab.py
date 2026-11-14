"""Small web-lab endpoints; the browser calls one comparison at a time."""
from datetime import datetime, timezone
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import Settings
from app.evaluation import grade
from app.experiments import EXPERIMENTS
from app.groq_service import GroqExtractionService
from app.offline_lab import run_offline_lab
from app.prompts import system_prompt
from app.schemas import ContactExtraction, Mode
from scenarios import EVALUATION_SCENARIOS

router = APIRouter(prefix="/lab", tags=["Classroom lab"])


class ComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=8000)
    prompt_a: str = Field(min_length=1, max_length=8000)
    prompt_b: str = Field(min_length=1, max_length=8000)
    expected: ContactExtraction | None = None
    case_id: str = Field(default="custom", max_length=30)
    mode: Mode = "prompt"
    repair: bool = False

    @field_validator("text", "prompt_a", "prompt_b")
    @classmethod
    def reject_blank(cls, value):
        if not value.strip():
            raise ValueError("Text and prompts must not be blank")
        return value.strip()


def get_lab_service():
    return GroqExtractionService


@router.get("/config")
def config():
    settings = Settings()
    return {
        "scenarios": EVALUATION_SCENARIOS,
        "experiments": EXPERIMENTS,
        "prompts": {v: system_prompt(v) for v in ("v1", "v2")},
        "models": {"prompt": settings.groq_model, "structured": settings.groq_structured_model},
        "schema": ContactExtraction.model_json_schema(),
    }


@router.post("/compare")
def compare(req: ComparisonRequest, factory=Depends(get_lab_service)):
    case = {"id": req.case_id, "text": req.text,
            "expected": req.expected.model_dump() if req.expected else None}
    result = {"case": case, "mode": req.mode, "repair_enabled": req.repair,
              "recorded_at_utc": datetime.now(timezone.utc).isoformat()}
    for label, version, prompt in [("a", "v1", req.prompt_a), ("b", "v2", req.prompt_b)]:
        try:
            service = factory(prompt_version=version, custom_system_prompt=prompt)
        except ValueError:
            raise HTTPException(503, "Configure GROQ_API_KEY on the backend.") from None
        try:
            row = grade(case, req.mode, service, repair=req.repair)
            # Save the exact prompt, not only a mutable label like 'v2'.
            row.update(model=service.model_for(req.mode), prompt=prompt,
                       prompt_hash=sha256(prompt.encode()).hexdigest()[:12])
            result[label] = row
        finally:
            service.client.close()
    return result


@router.post("/offline")
def offline():
    return {"live": False, "rows": run_offline_lab()}
