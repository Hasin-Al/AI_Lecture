from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Mode = Literal["prompt", "structured"]
PromptVersion = Literal["v1", "v2"]


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=8000)
    mode: Mode = "prompt"
    prompt_version: PromptVersion = "v1"
    repair: bool = False

    @field_validator("text")
    @classmethod
    def trim_source(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Source text must not be blank")
        return value


class ContactExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    # No defaults: every key is REQUIRED, even when its value is null.
    full_name: str | None = Field(description="Full name from source, or null.")
    email: str | None = Field(description="Email from source, or null.")
    phone: str | None = Field(description="Phone from source, preserving format, or null.")




class ExtractionResponse(BaseModel):
    request_id: str
    prompt_version: str
    model: str
    mode: Mode
    schema_valid: bool
    repaired: bool
    provider_calls: int
    evidence: dict[str, bool]
    data: ContactExtraction


class CustomerRecord(BaseModel):
    """Local tool-output exercise only; this app does not connect to a CRM."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    customer_id: str = Field(min_length=1)
    status: str
    credit_limit: float = Field(ge=0)
