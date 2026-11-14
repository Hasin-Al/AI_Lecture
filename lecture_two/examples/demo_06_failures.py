"""Section 13 / S11–S12: controlled failures and exactly one repair. No API calls."""
import json

from app.groq_service import ExtractionFailure, GroqExtractionService

GOOD = json.dumps({"full_name": "Mina Rahman", "email": "mina@example.com", "phone": None})
BAD_OUTPUTS = {
    "empty": "", "non-JSON": "not json", "truncated": '{"full_name":"Mina",',
    "missing key": '{"full_name":"Mina","email":null}',
    "extra key": '{"full_name":"Mina","email":null,"phone":null,"admin":true}',
    "wrong type": '{"full_name":"Mina","email":null,"phone":123}',
}


class ScriptedService(GroqExtractionService):
    """Reuse the real parse/repair flow; replace just the network methods."""
    def __init__(self, first, second):
        self.first, self.second = first, second
        self.call_count = 0

    def call_raw(self, source_text, mode):
        self.call_count += 1
        return self.first

    def call_repair(self, source_text, bad_output, problem, mode):
        self.call_count += 1
        return self.second


def main():
    for label, raw in BAD_OUTPUTS.items():
        try:
            GroqExtractionService.parse(raw)
        except ExtractionFailure as exc:
            print(label, "-> rejected:", exc)
    for label, first, second in [("already valid", GOOD, GOOD),
                                  ("repair succeeds", "broken", GOOD),
                                  ("repair fails", "broken", "still broken")]:
        service = ScriptedService(first, second)
        try:
            data, repaired = service.extract_with_repair("Mina Rahman mina@example.com", "prompt")
            print(label, "->", data.model_dump(), "repaired:", repaired)
        except ExtractionFailure:
            print(label, "-> controlled failure; no more repairs")
        print("  Simulated calls:", service.call_count)


if __name__ == "__main__":
    main()
