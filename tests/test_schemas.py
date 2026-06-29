from datetime import date

import pytest
from pydantic import ValidationError

from app.api.schemas.common import ComplianceScore
from app.api.schemas.extraction_schema import ExtractedClaimData, ExtractionRequest


def test_extracted_claim_data_accepts_valid_claim_fields() -> None:
    claim = ExtractedClaimData(
        claim_id="CLM-2026-00042",
        provider_id="PRV-1001",
        patient_id="PAT-2002",
        claim_date="2026-06-15",
        patient_name="Jane Doe",
        patient_dob="1988-04-23",
        provider_name="Example Behavioral Health",
        provider_license="LIC-908172",
        provider_npi="1234567890",
        service_dates=["2026-06-12"],
        session_start_time="09:00:00",
        session_end_time="10:00:00",
        session_duration_minutes=60,
        service_location="Outpatient clinic",
        cpt_codes=["90837"],
        modifiers=["GT"],
        place_of_service="11",
        diagnosis_codes=["F41.1"],
        billed_units=1,
        treatment_plan_date="2026-05-30",
        authorization_number="AUTH-7788",
        treatment_goals=["Reduce anxiety symptoms"],
        clinical_narrative="Patient participated in CBT session.",
        clinical_note_date="2026-06-12",
        provider_signature_present=True,
        dla20_deficiency_areas=["health_practices"],
        dla20_scores={"health_practices": 4},
        dla20_total_score=52,
        treatment_plan_raw="Treatment plan source text.",
        clinical_notes_raw="Clinical note source text.",
        dla20_raw="DLA-20 source text.",
    )

    assert claim.claim_date == date(2026, 6, 15)
    assert claim.cpt_codes == ["90837"]
    assert claim.diagnosis_codes == ["F41.1"]


@pytest.mark.parametrize("cpt_code", ["9083", "908370", "A0837"])
def test_cpt_codes_must_be_five_digits(cpt_code: str) -> None:
    with pytest.raises(ValidationError, match="CPT codes must be 5 digits"):
        ExtractedClaimData(cpt_codes=[cpt_code])


@pytest.mark.parametrize("diagnosis_code", ["41.1", "FF1.1", "F4112345", "U07.1"])
def test_diagnosis_codes_must_follow_basic_icd10_format(diagnosis_code: str) -> None:
    with pytest.raises(ValidationError, match="Diagnosis codes must follow basic ICD-10 format"):
        ExtractedClaimData(diagnosis_codes=[diagnosis_code])


def test_claim_date_must_be_valid_date() -> None:
    with pytest.raises(ValidationError):
        ExtractedClaimData(claim_date="2026-02-31")


@pytest.mark.parametrize("document_type", ["treatment_plan", "clinical_notes", "dla20"])
def test_extraction_request_accepts_supported_document_types(document_type: str) -> None:
    request = ExtractionRequest(
        claim_id="CLAIM-001",
        provider_id="PROV-001",
        patient_id="PAT-001",
        claim_date="2026-06-29",
        ocr_results=[{"document_type": document_type, "raw_text": "source text"}],
    )

    assert request.ocr_results[0].document_type == document_type


def test_extraction_request_rejects_unsupported_document_type() -> None:
    with pytest.raises(ValidationError):
        ExtractionRequest(
            claim_id="CLAIM-001",
            provider_id="PROV-001",
            patient_id="PAT-001",
            claim_date="2026-06-29",
            ocr_results=[{"document_type": "claim", "raw_text": "source text"}],
        )


@pytest.mark.parametrize("score", [0, 100])
def test_compliance_score_accepts_inclusive_bounds(score: int) -> None:
    compliance_score = ComplianceScore(
        compliance_score=score,
        risk_level="low",
        failed_rules=0,
        total_rules=1,
    )

    assert compliance_score.compliance_score == score


@pytest.mark.parametrize("score", [-1, 101])
def test_compliance_score_rejects_values_outside_bounds(score: int) -> None:
    with pytest.raises(ValidationError):
        ComplianceScore(
            compliance_score=score,
            risk_level="high",
            failed_rules=1,
            total_rules=1,
        )
