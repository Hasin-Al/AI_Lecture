"""Request and response contracts for the teaching API."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    temperature: float = Field(default=0.7, ge=0, le=2)


class ChatResponse(BaseModel):
    request_id: str
    response: str
    model: str


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


class SummarizeResponse(BaseModel):
    request_id: str
    summary: str
    model: str
