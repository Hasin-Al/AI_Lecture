"""Sections 8–9: inspect a real raw response, then parse and validate it."""
import argparse
import json

from app.evidence import evidence_report
from app.groq_service import GroqExtractionService
from app.schemas import ContactExtraction
from scenarios import SCENARIOS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["prompt", "structured"], default="prompt")
    parser.add_argument("--prompt-version", choices=["v1", "v2"], default="v1")
    parser.add_argument("--scenario", choices=[s["id"] for s in SCENARIOS], default="S1")
    args = parser.parse_args()
    case = next(s for s in SCENARIOS if s["id"] == args.scenario)
    service = GroqExtractionService(prompt_version=args.prompt_version)
    try:
        print("Source:", case["text"])
        print("Model:", service.model_for(args.mode), "Prompt:", args.prompt_version)
        raw = service.call_raw(case["text"], args.mode)
        print("\n1. Raw model output:\n", raw)
        parsed = json.loads(raw)
        print("\n2. JSON parsing passed")
        data = ContactExtraction.model_validate(parsed)
        print("\n3. Pydantic validation passed:\n", data.model_dump())
        print("\n4. Evidence:", evidence_report(data.model_dump(), case["text"]))
        print("Expected-answer match:", data.model_dump() == case["expected"])
    finally:
        service.client.close()


if __name__ == "__main__":
    main()
