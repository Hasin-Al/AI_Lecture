"""Pre-class check: key presence, configured models, and optional live access."""
import argparse

from groq import Groq, GroqError

from app.config import Settings
from app.groq_service import ExtractionFailure, GroqExtractionService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="List models and make two small extraction calls")
    args = parser.parse_args()
    settings = Settings()
    print("GROQ_API_KEY:", "set (hidden)" if settings.groq_api_key else "missing")
    print("Prompt model:", settings.groq_model)
    print("Structured model:", settings.groq_structured_model)
    if not args.live:
        print("No network calls. Add --live to check provider access.")
        return 0
    try:
        with Groq(api_key=settings.api_key(), timeout=20, max_retries=0) as client:
            available = {model.id for model in client.models.list().data}
            print("Available model IDs:", ", ".join(sorted(available)))
            ok = True
            service = GroqExtractionService(client=client, settings=settings, prompt_version="v2")
            for mode in ("prompt", "structured"):
                if service.model_for(mode) not in available:
                    print(mode, "FAIL: configured model is not available")
                    ok = False
                    continue
                try:
                    result = service.extract("Mina Rahman, mina@example.com", mode)
                    print(mode, "PASS:", result.model_dump())
                except (GroqError, ExtractionFailure) as exc:
                    print(mode, "FAIL:", type(exc).__name__)
                    ok = False
            return 0 if ok else 1
    except (ValueError, GroqError) as exc:
        print("Setup check failed:", type(exc).__name__)
        print("Check the key, model access, and network. No secrets were printed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
