from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.rule_engine.registry import get_all_rules, get_rule_count, validate_rule_registry
from tests.test_analyze_claim_api import _multipart_payload, _patch_fake_ocr
from tests.test_validation_api import _validation_payload


def test_health_endpoint_returns_stable_keys() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai/health")

    assert response.status_code == 200
    assert set(response.json()) == {"status", "service", "version", "environment"}


def test_validate_endpoint_returns_exactly_19_rule_results() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/ai/validate", json=_validation_payload())

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 19
    assert 0 <= body["compliance_score"] <= 100
    assert "score_band" in body
    assert "flag_summary" in body


def test_analyze_claim_response_has_stable_top_level_keys(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "claim_id",
        "ai_status",
        "compliance_score",
        "score_band",
        "ocr_summary",
        "extracted_data",
        "flag_summary",
        "rule_results",
        "metadata",
    }
    assert len(body["rule_results"]) == 19
    assert 0 <= body["compliance_score"] <= 100
    assert body["score_band"]
    assert set(body["flag_summary"]) == {"high", "medium", "low"}
    assert "processing_time_ms" in body["metadata"]


def test_request_id_header_exists() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_standard_error_response_shape_is_stable() -> None:
    client = TestClient(app)
    payload = _validation_payload()
    payload["extracted_data"]["cpt_codes"] = ["ABCDE"]  # type: ignore[index]

    response = client.post("/api/v1/ai/validate", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"status", "request_id", "error_code", "message", "details"}
    assert body["status"] == "error"
    assert body["request_id"]
    assert isinstance(body["details"], dict)


def test_rule_registry_contract_is_stable() -> None:
    rule_ids = [rule.rule_id for rule in get_all_rules()]

    assert get_rule_count() == 19
    assert validate_rule_registry() is True
    assert len(rule_ids) == len(set(rule_ids))


def test_no_database_dependency_is_required() -> None:
    compose_text = Path("docker-compose.yml").read_text(encoding="utf-8").lower()

    assert "ai-service" in compose_text
    assert "postgres" not in compose_text
    assert "mysql" not in compose_text
    assert "mongodb" not in compose_text
