import logging
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import ai_routes
from app.main import app
from app.services.ocr.base import OCRResult
from tests.test_analyze_claim_api import _multipart_payload


class _SensitiveOCRService:
    def extract_batch(self, file_paths: list[str], document_type: str) -> list[OCRResult]:
        raw_text = {
            "treatment_plan": "SENSITIVE_TREATMENT_PLAN_TEXT Reduce depression symptoms and self-care goals.",
            "clinical_notes": (
                "Clinical Narrative: SENSITIVE_CLINICAL_NARRATIVE Patient worked on depression coping skills, "
                "self-care, emotional regulation, communication, housing tasks, community supports, sleep hygiene, "
                "safety planning, daily structure, family stress, and treatment goals during the session. "
                "Provider Signature: Signed by clinician. Service Date: 06/29/2026. Session Time: 10:00 - 11:00. "
                "CPT: 90837-HN. Diagnosis: F32.1. Billed Units: 4. Place of Service: 11. Provider License: LICSW."
            ),
            "dla20": "SENSITIVE_DLA20_TEXT Coping Skills: 2 Housing Stability: 2 DLA-20 Total Score: 2",
        }[document_type]
        return [
            OCRResult(
                document_id=f"{document_type}-{index}",
                document_type=document_type,
                file_name=Path(file_path).name,
                raw_text=raw_text,
                page_count=1,
                confidence=1.0,
                metadata={"method": "fake", "provider": "test"},
            )
            for index, file_path in enumerate(file_paths, start=1)
        ]


def test_request_id_from_header_is_preserved() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai/health", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"


def test_generated_request_id_exists_if_header_missing() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_raw_ocr_text_is_not_present_in_logs(monkeypatch: MonkeyPatch, caplog) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(ai_routes, "get_ocr_service", lambda: _SensitiveOCRService())
    client = TestClient(app)
    data, files = _multipart_payload()
    caplog.set_level(logging.INFO, logger="app")

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 200
    assert "SENSITIVE_TREATMENT_PLAN_TEXT" not in caplog.text
    assert "SENSITIVE_CLINICAL_NARRATIVE" not in caplog.text
    assert "SENSITIVE_DLA20_TEXT" not in caplog.text
    assert any(getattr(record, "claim_id", None) == "CLAIM-001" for record in caplog.records)
    assert any(
        getattr(record, "endpoint", None) == "/api/v1/ai/analyze-claim"
        for record in caplog.records
    )
