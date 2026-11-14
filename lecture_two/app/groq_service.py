import json

from groq import Groq
from pydantic import ValidationError

from app.config import Settings
from app.prompts import REPAIR_PROMPT, messages_for
from app.retry import with_retry
from app.schemas import ContactExtraction


class ExtractionFailure(Exception):
    """Safe error description; never includes the raw provider response."""


class GroqExtractionService:
    def __init__(self, client=None, settings=None, prompt_version="v1", custom_system_prompt=None):
        self.settings = settings or Settings()
        self.prompt_version = prompt_version
        self.custom_system_prompt = custom_system_prompt
        self.client = client or Groq(
            api_key=self.settings.api_key(), timeout=20, max_retries=0,
        )
        self.call_count = 0

    def model_for(self, mode: str) -> str:
        if mode not in ("prompt", "structured"):
            raise ValueError("Mode must be prompt or structured")
        return (self.settings.groq_structured_model if mode == "structured"
                else self.settings.groq_model)

    def _chat(self, messages: list, mode: str) -> str:
        params = {"model": self.model_for(mode), "messages": messages,
                  "temperature": 0, "max_completion_tokens": 2048}
        if mode == "structured":
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "contact_extraction", "strict": True,
                    "schema": ContactExtraction.model_json_schema(),
                },
            }

        def send(remaining_seconds):
            self.call_count += 1  # Count actual requests, including retries.
            return self.client.chat.completions.create(
                **params, timeout=min(20, remaining_seconds),
            )

        response = with_retry(send)
        if not response.choices:
            raise ExtractionFailure("Provider returned no choices")
        choice = response.choices[0]
        if choice.finish_reason != "stop" or getattr(choice.message, "refusal", None):
            raise ExtractionFailure("Provider response was incomplete or refused")
        return choice.message.content or ""

    def _messages(self, source_text: str) -> list[dict]:
        messages = messages_for(source_text, self.prompt_version)
        if self.custom_system_prompt is not None:
            messages[0]["content"] = self.custom_system_prompt
        return messages

    def call_raw(self, source_text: str, mode: str) -> str:
        return self._chat(self._messages(source_text), mode)

    def call_repair(self, source_text: str, bad_output: str, problem: str, mode: str) -> str:
        messages = self._messages(source_text)
        # Retain all original trusted rules, including the v2 ambiguity policy.
        messages[0]["content"] += "\n\n" + REPAIR_PROMPT
        messages[1]["content"] = json.dumps({
            "original_source": source_text, "invalid_output": bad_output,
            "validation_problem": problem,
        })
        return self._chat(messages, mode)

    @staticmethod
    def parse(raw: str) -> ContactExtraction:
        if not raw or not raw.strip():
            raise ExtractionFailure("Empty model response")
        try:
            parsed = json.loads(raw)  # 1. Syntax
        except json.JSONDecodeError as exc:
            raise ExtractionFailure("Invalid JSON syntax") from exc
        try:
            return ContactExtraction.model_validate(parsed)  # 2. Structure
        except ValidationError as exc:
            raise ExtractionFailure("JSON did not match the contact schema") from exc

    def extract(self, source_text: str, mode: str) -> ContactExtraction:
        return self.parse(self.call_raw(source_text, mode))

    def extract_with_repair(self, source_text: str, mode: str):
        raw = self.call_raw(source_text, mode)
        try:
            return self.parse(raw), False
        except ExtractionFailure as exc:
            problem = str(exc)
        repaired_raw = self.call_repair(source_text, raw, problem, mode)
        return self.parse(repaired_raw), True  # Never attempt a second repair.
