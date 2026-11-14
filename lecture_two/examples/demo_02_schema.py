"""Section 6: JSON syntax, Pydantic validation, and generated JSON Schema. Offline."""
import json

from pydantic import ValidationError

from app.schemas import ContactExtraction


def main():
    good = {"full_name": "Mina Rahman", "email": "mina@example.com", "phone": None}
    samples = {
        "valid": json.dumps(good),
        "invalid JSON": "not json",
        "missing key": json.dumps({"full_name": "Mina", "email": None}),
        "wrong type": json.dumps({**good, "phone": 123}),
        "extra key": json.dumps({**good, "admin": True}),
    }
    for label, raw in samples.items():
        print(f"\n{label}: {raw}")
        try:
            payload = json.loads(raw)
            print("  JSON syntax: PASS")
            result = ContactExtraction.model_validate(payload)
            print("  Schema: PASS", result.model_dump())
        except json.JSONDecodeError:
            print("  JSON syntax: FAIL")
        except ValidationError as exc:
            print("  Schema: FAIL", exc.errors(include_url=False, include_input=False))
    print("\nGenerated JSON Schema:")
    print(json.dumps(ContactExtraction.model_json_schema(), indent=2))


if __name__ == "__main__":
    main()
