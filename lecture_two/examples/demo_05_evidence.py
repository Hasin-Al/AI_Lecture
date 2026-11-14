"""Section 12: valid shape and source presence still do not prove correctness. Offline."""
from app.evidence import evidence_report
from app.schemas import ContactExtraction
from scenarios import SCENARIOS


def main():
    for case, email in [(SCENARIOS[7], "imran@invented.example"),
                        (SCENARIOS[6], "attacker@example.com")]:
        data = ContactExtraction.model_validate({**case["expected"], "email": email})
        print("\n", case["id"], case["text"])
        print("Controlled wrong answer:", data.model_dump())
        print("Schema: PASS")
        print("Evidence:", evidence_report(data.model_dump(), case["text"]))
        print("Expected-answer match:", data.model_dump() == case["expected"])
    print("\nS8 catches fabrication. S7 passes source presence but selects the wrong email.")
    print("This is a deterministic demonstration, not an observed live-model failure.")


if __name__ == "__main__":
    main()
