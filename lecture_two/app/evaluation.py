"""Shared grading for the command-line runner and the FastAPI classroom lab."""
import json
import time

from pydantic import ValidationError

from app.evidence import evidence_report
from app.schemas import ContactExtraction


def grade(case: dict, mode: str, service, repair=False) -> dict:
    row = {"id": case["id"], "mode": mode, "source": case["text"],
           "expected": case["expected"], "parse": False, "schema": False,
           "final_schema": False, "evidence": False,
           "match": False if case["expected"] is not None else None,
           "correct_fields": 0, "repair_attempted": False,
           "raw": None, "repaired_raw": None, "data": None, "note": ""}
    started, calls_before = time.monotonic(), service.call_count
    try:
        raw = service.call_raw(case["text"].strip(), mode)
        row["raw"] = raw
        try:
            payload = json.loads(raw)
            row["parse"] = True
            data = ContactExtraction.model_validate(payload)
            row["schema"] = True
        except (json.JSONDecodeError, ValidationError) as exc:
            row["note"] = "First output: " + type(exc).__name__
            if not repair:
                return row
            row["repair_attempted"] = True
            raw = service.call_repair(case["text"].strip(), raw, row["note"], mode)
            row["repaired_raw"] = raw
            data = service.parse(raw)  # The second failure ends this case.
        row["data"] = data.model_dump()
        row["final_schema"] = True
        row["evidence"] = all(evidence_report(row["data"], case["text"]).values())
        if case["expected"] is not None:
            row["match"] = row["data"] == case["expected"]
            row["correct_fields"] = sum(row["data"][key] == value
                                        for key, value in case["expected"].items())
            if not row["match"]:
                row["note"] += " Expected-answer mismatch"
    except Exception as exc:
        # A provider outage must count as a failed case, not disappear from N.
        # Do not persist exception bodies, which may contain provider internals.
        row["note"] += " " + type(exc).__name__
    finally:
        row["seconds"] = round(time.monotonic() - started, 3)
        row["calls"] = service.call_count - calls_before
    return row


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    first = sum(r["schema"] for r in rows)
    final = sum(r["final_schema"] for r in rows)
    repairs = sum(r["repair_attempted"] for r in rows)
    calls = sum(r["calls"] for r in rows)
    scored = sum(r["match"] is not None for r in rows)
    return {
        "cases": n, "first_valid": first, "final_valid": final,
        "first_valid_pct": round(100 * first / n, 2) if n else 0,
        "final_valid_pct": round(100 * final / n, 2) if n else 0,
        "scored_cases": scored,
        "exact_matches": sum(r["match"] is True for r in rows),
        "correct_fields": sum(r["correct_fields"] for r in rows),
        "fields_evaluated": 3 * scored,
        "field_accuracy_pct": round(100 * sum(r["correct_fields"] for r in rows) / (3 * scored), 2) if scored else None,
        "repair_cases": repairs, "repair_rate_pct": round(100 * repairs / n, 2) if n else 0,
        "average_seconds": round(sum(r["seconds"] for r in rows) / n, 3) if n else 0,
        "calls": calls, "calls_per_success": round(calls / final, 3) if final else None,
    }


