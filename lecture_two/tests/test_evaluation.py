import json

import pytest

from app.schemas import ContactExtraction
from run_scenarios import grade, summarize
from scenarios import EVALUATION_SCENARIOS, SCENARIOS
from test_service import make_service


@pytest.mark.parametrize("case", EVALUATION_SCENARIOS, ids=lambda c: c["id"])
def test_expected_answers_are_schema_valid(case):
    # This checks the fixture contract, not a model's ability to extract it.
    assert ContactExtraction.model_validate(case["expected"]).model_dump() == case["expected"]


def test_first_failure_is_not_hidden_by_repair():
    case = SCENARIOS[0]
    service = make_service(["broken", json.dumps(case["expected"])])
    row = grade(case, "prompt", service, repair=True)
    assert not row["schema"] and not row["parse"]
    assert row["final_schema"] and row["match"] and row["repair_attempted"]
    assert row["calls"] == 2 and row["correct_fields"] == 3
    metrics = summarize([row])
    assert metrics["first_valid"] == 0 and metrics["final_valid"] == 1
    assert metrics["calls_per_success"] == 2


def test_failed_repair_and_provider_failure_stay_in_denominator():
    bad = grade(SCENARIOS[0], "prompt", make_service(["bad", "bad"]), repair=True)
    service = make_service([])
    def unavailable(*args):
        service.call_count += 1
        raise ConnectionError("do not leak this body")
    service.call_raw = unavailable
    unavailable_row = grade(SCENARIOS[0], "prompt", service)
    metrics = summarize([bad, unavailable_row])
    assert metrics["cases"] == 2 and metrics["final_valid"] == 0
    assert metrics["calls"] == 3 and metrics["calls_per_success"] is None
    assert metrics["field_accuracy_pct"] == 0
    assert unavailable_row["seconds"] >= 0
    assert "do not leak" not in json.dumps(unavailable_row)


def test_evidence_does_not_replace_expected_answer():
    case = SCENARIOS[6]
    wrong = {**case["expected"], "email": "attacker@example.com"}
    row = grade(case, "prompt", make_service([json.dumps(wrong)]))
    assert row["schema"] and row["evidence"] and not row["match"]
    assert row["correct_fields"] == 2


def test_twenty_unique_cases():
    assert len(EVALUATION_SCENARIOS) == 20
    assert len({case["id"] for case in EVALUATION_SCENARIOS}) == 20


def test_unscored_custom_input_does_not_inflate_accuracy():
    case = {"id": "custom", "text": "Mina", "expected": None}
    raw = '{"full_name":"Mina","email":null,"phone":null}'
    row = grade(case, "prompt", make_service([raw]))
    metrics = summarize([row])
    assert metrics["final_valid"] == 1
    assert metrics["scored_cases"] == 0
    assert metrics["field_accuracy_pct"] is None
