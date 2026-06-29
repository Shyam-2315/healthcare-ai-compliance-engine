from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import ai_routes
from app.main import app
from tests.test_analyze_claim_api import _multipart_payload, _patch_fake_ocr


def test_health_response_includes_request_id_header() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_invalid_payload_returns_json_safe_error() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/ai/validate",
        json={
            "claim_id": "CLAIM-001",
            "provider_id": "PROV-001",
            "patient_id": "PAT-001",
            "claim_date": "2026-06-29",
            "extracted_data": {"cpt_codes": ["ABCDE"]},
            "bhs_matrix": [],
            "cpt_credentials": [],
            "historical_claims": [],
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["request_id"]
    assert isinstance(body["details"]["errors"][0]["ctx"]["error"], str)


def test_unsupported_file_type_returns_standard_error_format(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    files[0] = ("treatment_plan_files", ("bad.txt", b"bad", "text/plain"))

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "UNSUPPORTED_FILE_TYPE"
    assert body["request_id"]
    assert isinstance(body["details"], dict)


def test_invalid_master_data_json_returns_standard_error_format(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    data["bhs_matrix_json"] = "{bad json"

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "INVALID_MASTER_DATA"
    assert body["request_id"]


def test_missing_required_files_returns_standard_error_format(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    files = [item for item in files if item[0] != "treatment_plan_files"]

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "MISSING_REQUIRED_FILES"
    assert body["request_id"]


def test_ocr_runtime_error_returns_standard_error_format(monkeypatch: MonkeyPatch) -> None:
    class _ExplodingOCRService:
        def extract_batch(self, file_paths: list[str], document_type: str):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom secret text")

    monkeypatch.setattr(ai_routes, "get_ocr_service", lambda: _ExplodingOCRService())
    client = TestClient(app)
    data, files = _multipart_payload()

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "OCR_FAILED"
    assert body["request_id"]
    assert "boom secret text" not in response.text


def test_unexpected_exception_returns_safe_error_shape(monkeypatch: MonkeyPatch) -> None:
    def _explode_rule_engine(self, extracted, bhs_matrix, cpt_credentials, historical_claims):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom secret text")

    monkeypatch.setattr(ai_routes.RuleEngine, "run", _explode_rule_engine)
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    data, files = _multipart_payload()

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "INTERNAL_ERROR"
    assert body["request_id"]
    assert body["message"] == "An unexpected internal error occurred."
    assert "boom secret text" not in response.text
