"""A deliberately simple heuristic: source presence does NOT prove correctness."""
import re


def supported(field: str, value: str|  None, source: str) -> bool:
    if value is None:
        return True  # Null makes no factual claim; it may still be the wrong answer.

    # if isinstance(value, list):
    #     return bool(value) and all(
    #         supported(field, item, source)
    #         for item in value
    #     )
    
    if not value.strip():
        return False
    if field == "phone":
        digits = re.sub(r"\D", "", value)
        return bool(digits) and digits in re.sub(r"\D", "", source)
    if field == "email":
        return value.casefold() in source.casefold()
    if field == "full_name":
        return all(word.casefold() in source.casefold() for word in value.split())
    return False


def evidence_report(data: dict, source: str) -> dict[str, bool]:
    return {field: supported(field, value, source) for field, value in data.items()}
