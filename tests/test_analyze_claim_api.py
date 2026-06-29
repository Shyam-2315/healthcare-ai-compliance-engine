import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pytest import MonkeyPatch
from fastapi.testclient import TestClient

from app.api.routes import ai_routes
from app.main import app
from app.services.ocr.base import OCRResult
from app.utils.file_utils import cleanup_temp_files as real_cleanup_temp_files


class _FakeOCRService:
    def extract_batch(self, file_paths: list[str], document_type: str) -> list[OCRResult]:
        text_by_type = {
            "treatment_plan": (
                "Treatment Plan Date: 2026-05-01\n"
                "Authorization Number: AUTH-2026-4451\n"
                "Goals:\n"
                "- Improve coping skills\n"
                "- Stabilize housing\n"
            ),
            "clinical_notes": (
                "Patient Name: Jane Doe\n"
                "Date of Birth: 04/23/1988\n"
                "Provider Name: Example Clinic\n"
                "Provider License: LICSW\n"
                "Clinical Note Date: 2026-06-29\n"
                "Service Date: 06/29/2026\n"
                "Session Time: 10:00 - 11:00\n"
                "Service Location: Clinic A\n"
                "Place of Service: 11\n"
                "CPT: 90837-HN\n"
                "Diagnosis: F32.1\n"
                "Billed Units: 4\n"
                "Clinical Narrative: The patient practiced coping skills, reviewed housing stability "
                "tasks, discussed daily living routines, addressed emotional regulation, planned community "
                "support follow up, reinforced communication strategies, explored family stress, "
                "reviewed self-care steps, and connected each intervention directly to the documented "
                "treatment goals during the session while the provider assessed response and next steps.\n"
                "Provider Signature: Jane Smith\n"
            ),
            "dla20": (
                "Coping Skills: 2\n"
                "Housing Stability: 2\n"
                "DLA-20 Total Score: 2\n"
            ),
        }
        return [
            OCRResult(
                document_id=f"{document_type}-{index}",
                document_type=document_type,
                file_name=Path(file_path).name,
                raw_text=text_by_type[document_type],
                page_count=1,
                confidence=1.0,
                metadata={"method": "fake", "provider": "test"},
            )
            for index, file_path in enumerate(file_paths, start=1)
        ]


def _docx_bytes(text: str) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                "</Types>"
            ),
        )
        archive.writestr(
            "_rels/.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="word/document.xml"/>'
                "</Relationships>"
            ),
        )
        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
            ),
        )
    return buffer.getvalue()


def _multipart_payload() -> tuple[dict[str, str], list[tuple[str, tuple[str, bytes, str]]]]:
    data = {
        "claim_id": "CLAIM-001",
        "provider_id": "PROV-001",
        "patient_id": "PAT-001",
        "claim_date": "2026-06-29",
        "bhs_matrix_json": json.dumps(
            [
                {
                    "proc_code": "90837",
                    "mod1": "HN",
                    "mod2": None,
                    "mod3": None,
                    "mod4": None,
                    "pos_allowed": "11,02",
                    "icd10": "F32.1,F41.1",
                }
            ]
        ),
        "cpt_credentials_json": json.dumps([{"cpt_code": "90837", "license": "LICSW"}]),
        "historical_claims_json": "[]",
    }
    files = [
        (
            "treatment_plan_files",
            (
                "treatment-plan.docx",
                _docx_bytes("Treatment plan"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ),
        (
            "clinical_note_files",
            (
                "clinical-note.docx",
                _docx_bytes("Clinical note"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ),
        (
            "dla20_files",
            (
                "dla20.docx",
                _docx_bytes("DLA20"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ),
    ]
    return data, files


def _patch_fake_ocr(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(ai_routes, "get_ocr_service", lambda: _FakeOCRService())


def test_successful_analyze_claim_using_generated_docx_files(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "CLAIM-001"
    assert body["ai_status"] == "validated"
    assert body["extracted_data"]["claim_id"] == "CLAIM-001"
    assert len(body["rule_results"]) == 19
    assert 0 <= body["compliance_score"] <= 100
    assert body["score_band"]
    assert set(body["flag_summary"]) == {"high", "medium", "low"}
    assert "processing_time_ms" in body["metadata"]


def test_invalid_bhs_matrix_json_returns_clean_error(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    data["bhs_matrix_json"] = "{bad json"

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "INVALID_MASTER_DATA"


def test_invalid_cpt_credentials_json_returns_clean_error(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    data["cpt_credentials_json"] = "{bad json"

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "INVALID_MASTER_DATA"


def test_invalid_historical_claims_json_returns_clean_error(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    data["historical_claims_json"] = "{bad json"

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "INVALID_MASTER_DATA"


def test_missing_treatment_plan_files_returns_clean_error(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    files = [item for item in files if item[0] != "treatment_plan_files"]

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "MISSING_REQUIRED_FILES"


def test_missing_clinical_note_files_returns_clean_error(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    files = [item for item in files if item[0] != "clinical_note_files"]

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "MISSING_REQUIRED_FILES"


def test_missing_dla20_files_returns_clean_error(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    files = [item for item in files if item[0] != "dla20_files"]

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "MISSING_REQUIRED_FILES"


def test_unsupported_file_type_returns_clean_error(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    client = TestClient(app)
    data, files = _multipart_payload()
    files[0] = ("treatment_plan_files", ("bad.txt", b"bad", "text/plain"))

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert body["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_temp_files_are_cleaned_up_after_success(monkeypatch: MonkeyPatch) -> None:
    _patch_fake_ocr(monkeypatch)
    cleaned_paths: list[str] = []

    def cleanup_wrapper(file_paths: list[str]) -> None:
        cleaned_paths.extend(file_paths)
        real_cleanup_temp_files(file_paths)

    monkeypatch.setattr(ai_routes, "cleanup_temp_files", cleanup_wrapper)
    client = TestClient(app)
    data, files = _multipart_payload()

    response = client.post("/api/v1/ai/analyze-claim", data=data, files=files)

    assert response.status_code == 200
    assert len(cleaned_paths) == 3
    assert all(not Path(path).exists() for path in cleaned_paths)
