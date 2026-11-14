"""Live evaluation, kept separate from pytest. Run --help for class options."""
import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.evaluation import grade, summarize
from app.groq_service import GroqExtractionService
from app.prompts import system_prompt
from app.schemas import ContactExtraction
from scenarios import EVALUATION_SCENARIOS, SCENARIOS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modes", nargs="*", help="prompt and/or structured (default: both)")
    parser.add_argument("--prompt-version", choices=["v1", "v2"], default="v1")
    parser.add_argument("--cases", choices=["lab", "full"], default="lab")
    parser.add_argument("--repair", action="store_true", help="Allow one repair of invalid output")
    parser.add_argument("--limit", type=int, help="Run only the first N cases for a quick check")
    parser.add_argument("--delay", type=float, default=0, help="Pause between cases to reduce rate limiting")
    parser.add_argument("--output", type=Path, help="Output base path, e.g. results/v1-prompt")
    args = parser.parse_args()
    modes = args.modes or ["prompt", "structured"]
    if any(mode not in ("prompt", "structured") for mode in modes):
        parser.error("Modes must be prompt or structured")
    if (args.limit is not None and args.limit < 1) or args.delay < 0:
        parser.error("limit must be positive and delay must be nonnegative")
    cases = (SCENARIOS if args.cases == "lab" else EVALUATION_SCENARIOS)[:args.limit]
    settings = Settings()
    try:
        service = GroqExtractionService(settings=settings, prompt_version=args.prompt_version)
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
    rows, metrics = [], {}
    try:
        for mode in modes:
            mode_rows = []
            print(f"\n{mode} | {service.model_for(mode)} | contact-extraction-{args.prompt_version}", flush=True)
            print("ID   JSON schema final evidence match calls seconds", flush=True)
            for case in cases:
                row = grade(case, mode, service, repair=args.repair)
                mode_rows.append(row)
                flags = " ".join(f"{int(row[key]):>5}" for key in
                                 ("parse", "schema", "final_schema", "evidence", "match"))
                print(f"{row['id']:<4} {flags} {row['calls']:>5} {row['seconds']:>7} {row['note']}", flush=True)
                if args.delay:
                    time.sleep(args.delay)
            metrics[mode] = summarize(mode_rows)
            rows.extend(mode_rows)
            print(json.dumps(metrics[mode], indent=2), flush=True)
    finally:
        service.client.close()
    now = datetime.now(timezone.utc)
    output = args.output or Path("results") / (now.strftime("%Y%m%dT%H%M%S%fZ") + "-" + args.prompt_version)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"recorded_at_utc": now.isoformat(), "prompt_version": "contact-extraction-" + args.prompt_version,
              "models": {mode: service.model_for(mode) for mode in modes},
              "system_prompt": system_prompt(args.prompt_version),
              "schema": ContactExtraction.model_json_schema(), "repair_enabled": args.repair,
              "metrics": metrics, "rows": rows}
    output.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, dict) else v for k, v in row.items()})
    print(f"\nSaved {output.with_suffix('.json')} and {output.with_suffix('.csv')}")
    # Mismatches are observations, not execution failures. Provider/output failures
    # still give a nonzero exit status, useful for the pre-class check.
    return 0 if all(row["final_schema"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
