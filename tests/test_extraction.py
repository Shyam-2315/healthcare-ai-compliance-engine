from datetime import date, time

from fastapi.testclient import TestClient

from app.api.schemas.extraction_schema import ExtractedClaimData, OCRTextInput
from app.main import app
from app.services.ai.local_ai import LocalDeterministicAI


def _extract() -> ExtractedClaimData:
    return LocalDeterministicAI().extract(
        [
            OCRTextInput(
                document_type="treatment_plan",
                raw_text=(
                    "Treatment Plan Date: June 1 2026\n"
                    "Authorization #: AUTH-789\n"
                    "Goals:\n"
                    "- Improve coping skills\n"
                    "Goal 2: Attend weekly therapy\n"
                ),
            ),
            OCRTextInput(
                document_type="clinical_notes",
                raw_text=(
                    "Patient Name: Jane Doe\n"
                    "Date of Birth: 04/23/1988\n"
                    "Provider Name: Example Behavioral Health\n"
                    "Provider License: LIC-908172\n"
                    "NPI: 1234567890\n"
                    "Clinical Note Date: 2026-06-29\n"
                    "Service Date: 06-29-2026\n"
                    "Session Time: 9:30 AM - 11:00 AM\n"
                    "Service Location: Outpatient Clinic\n"
                    "Place of Service: 11\n"
                    "CPT: 90837-HN\n"
                    "Diagnosis: F32.1, F41.1, Z63.0\n"
                    "Billed Units: 1\n"
                    "Clinical Narrative: Patient engaged in CBT intervention.\n"
                    "Electronically signed by Dr. Smith\n"
                ),
            ),
            OCRTextInput(
                document_type="dla20",
                raw_text=(
                    "DLA-20 Assessment\n"
                    "Health Practices: 2\n"
                    "Housing Stability: 4\n"
                    "Communication score 3\n"
                    "DLA-20 Total Score: 42\n"
                ),
            ),
        ],
        claim_context={
            "claim_id": "CLAIM-001",
            "provider_id": "PROV-001",
            "patient_id": "PAT-001",
            "claim_date": "2026-06-29",
        },
    )


def test_cpt_modifier_and_icd10_extraction() -> None:
    result = _extract()

    assert result.cpt_codes == ["90837"]
    assert result.modifiers == ["HN"]
    assert result.diagnosis_codes == ["F32.1", "F41.1", "Z63.0"]


def test_authorization_and_date_extraction() -> None:
    result = _extract()

    assert result.authorization_number == "AUTH-789"
    assert result.claim_date == date(2026, 6, 29)
    assert result.treatment_plan_date == date(2026, 6, 1)
    assert result.clinical_note_date == date(2026, 6, 29)
    assert result.service_dates == [date(2026, 6, 29)]


def test_time_extraction_and_session_duration_with_ampm() -> None:
    result = _extract()

    assert result.session_start_time == time(9, 30)
    assert result.session_end_time == time(11, 0)
    assert result.session_duration_minutes == 90


def test_provider_signature_and_treatment_goal_extraction() -> None:
    result = _extract()

    assert result.provider_signature_present is True
    assert result.treatment_goals == ["Improve coping skills", "Attend weekly therapy"]


def test_dla20_score_extraction() -> None:
    result = _extract()

    assert result.dla20_scores == {
        "communication": 3,
        "health_practices": 2,
        "housing_stability": 4,
    }
    assert result.dla20_deficiency_areas == ["communication", "health_practices"]
    assert result.dla20_total_score == 42


def test_raw_text_separation_by_document_type() -> None:
    result = _extract()

    assert result.treatment_plan_raw is not None
    assert "Authorization #: AUTH-789" in result.treatment_plan_raw
    assert result.clinical_notes_raw is not None
    assert "Clinical Narrative" in result.clinical_notes_raw
    assert result.dla20_raw is not None
    assert "DLA-20 Assessment" in result.dla20_raw


def test_claim_context_fields_are_not_guessed_from_documents() -> None:
    result = LocalDeterministicAI().extract(
        [
            OCRTextInput(
                document_type="clinical_notes",
                raw_text="Claim ID: WRONG Provider ID: WRONG Patient ID: WRONG Service Date: 06/29/2026",
            )
        ],
        claim_context={
            "claim_id": "CLAIM-001",
            "provider_id": "PROV-001",
            "patient_id": "PAT-001",
            "claim_date": "2026-06-29",
        },
    )

    assert result.claim_id == "CLAIM-001"
    assert result.provider_id == "PROV-001"
    assert result.patient_id == "PAT-001"


def test_extraction_api_response_shape() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/extract",
        json={
            "claim_id": "CLAIM-001",
            "provider_id": "PROV-001",
            "patient_id": "PAT-001",
            "claim_date": "2026-06-29",
            "ocr_results": [
                {
                    "document_type": "clinical_notes",
                    "raw_text": "Service Date: 06/29/2026\nCPT: 90837-HN\nDiagnosis: F41.1",
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "CLAIM-001"
    assert body["provider_id"] == "PROV-001"
    assert body["patient_id"] == "PAT-001"
    assert body["claim_date"] == "2026-06-29"
    assert body["cpt_codes"] == ["90837"]
    assert body["modifiers"] == ["HN"]
    assert body["diagnosis_codes"] == ["F41.1"]
