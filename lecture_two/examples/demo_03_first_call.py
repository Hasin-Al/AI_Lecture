"""Section 7: one real Groq SDK call. Requires .env and internet."""
import argparse

from groq import Groq

from app.config import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temperature", type=float, default=0)
    args = parser.parse_args()
    settings = Settings()
    with Groq(api_key=settings.api_key(), timeout=20, max_retries=0) as client:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": "Explain an API in one sentence."}],
            temperature=args.temperature,
        )
    choice = response.choices[0]
    print("model:", settings.groq_model)
    print("finish_reason:", choice.finish_reason)
    print("content:", choice.message.content)
    print("Temperature 0 reduces randomness; it does not guarantee correctness.")


if __name__ == "__main__":
    main()
