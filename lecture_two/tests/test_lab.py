import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.lab import get_lab_service
from app.main import app
from app.groq_service import GroqExtractionService
from app.prompts import system_prompt
from test_service import make_service


class FakeLabService:
    instances = []

    def __init__(self, prompt_version, custom_system_prompt):
        self.prompt = custom_system_prompt
        self.call_count = 0
        self.closed = False
        self.client = SimpleNamespace(close=self.close)
        self.instances.append(self)

    def close(self):
        self.closed = True

    def model_for(self, mode):
        return "same-model"

    def call_raw(self, source, mode):
        self.call_count += 1
        return json.dumps({"full_name": "Mina Rahman", "email": None, "phone": None})


@pytest.fixture
def client():
    FakeLabService.instances.clear()
    app.dependency_overrides[get_lab_service] = lambda: FakeLabService
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def payload(**changes):
    return {"text": "Mina Rahman", "prompt_a": system_prompt("v1"),
            "prompt_b": system_prompt("v2"), **changes}


def test_web_app_and_catalog(client):
    assert client.get("/").status_code == 200
    assert "Prompt lab" in client.get("/").text
    assert client.get("/static/lab.js").status_code == 200
    config = client.get("/lab/config").json()
    assert len(config["scenarios"]) == 20
    assert config["prompts"]["v2"] == system_prompt("v2")
    assert "api_key" not in json.dumps(config).lower()


def test_guided_experiments_change_only_one_rule(client):
    catalog = client.get("/lab/config").json()
    experiments = catalog["experiments"]
    cases = {case["id"]: case for case in catalog["scenarios"]}
    assert len(experiments) == 6
    assert len({item["id"] for item in experiments}) == 6
    for item in experiments:
        assert item["scenario_id"] in cases
        assert item["prompt_b"] == item["prompt_a"] + "\n\n" + item["rule"]
        assert item["rule"] not in item["prompt_a"]
        # Keep source-specific answers out of the instruction text.
        expected = cases[item["scenario_id"]]["expected"]
        for value in expected.values():
            if value is not None:
                assert value not in item["prompt_b"]


def test_compare_same_source_and_model_and_close_clients(client):
    expected = {"full_name": "Mina Rahman", "email": None, "phone": None}
    response = client.post("/lab/compare", json=payload(expected=expected))
    assert response.status_code == 200
    result = response.json()
    assert result["a"]["match"] and result["b"]["match"]
    assert result["a"]["model"] == result["b"]["model"]
    assert result["a"]["prompt"] == system_prompt("v1")
    assert result["b"]["prompt"] == system_prompt("v2")
    assert all(s.closed for s in FakeLabService.instances)


def test_custom_source_without_expected_answer_is_not_scored(client):
    response = client.post("/lab/compare", json=payload())
    result = response.json()
    assert result["a"]["match"] is None
    assert result["b"]["match"] is None
    assert result["a"]["schema"] is True


@pytest.mark.parametrize("changes", [
    {"text": " "}, {"text": "x" * 8001}, {"prompt_a": " "},
    {"prompt_b": "x" * 8001}, {"mode": "invalid"},
    {"expected": {"email": None}},
])
def test_invalid_comparison_never_creates_provider(client, changes):
    assert client.post("/lab/compare", json=payload(**changes)).status_code == 422
    assert FakeLabService.instances == []


def test_provider_failure_counts_as_failed_scored_case(client, monkeypatch):
    def fail(self, *args):
        self.call_count += 1
        raise ConnectionError("private provider body")
    monkeypatch.setattr(FakeLabService, "call_raw", fail)
    response = client.post("/lab/compare", json=payload(expected={
        "full_name": "Mina Rahman", "email": None, "phone": None,
    }))
    assert response.status_code == 200
    assert response.json()["a"]["match"] is False
    assert response.json()["a"]["calls"] == 1
    assert "private provider body" not in response.text


def test_custom_prompt_reaches_sdk_and_repair():
    base = make_service(["broken", '{"full_name":null,"email":null,"phone":null}'])
    service = GroqExtractionService(client=base.client, settings=base.settings,
                                    custom_system_prompt="My teaching rules")
    service.extract_with_repair("untrusted source", "prompt")
    assert base.client.params[0]["messages"][0]["content"] == "My teaching rules"
    assert base.client.params[1]["messages"][0]["content"].startswith("My teaching rules")
    assert base.client.params[0]["messages"][1]["content"] == "SOURCE TEXT:\nuntrusted source"


def test_all_offline_lecture_scenarios(client):
    response = client.post("/lab/offline")
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert {r["id"] for r in rows} == {"S10", "S11", "S12", "S13", "S14", "S15"}
    assert all(row["passed"] for row in rows)
    assert FakeLabService.instances == []
