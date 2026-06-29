import re
from datetime import date, time
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from app.api.schemas.common import APIModel

DocumentType = Literal["treatment_plan", "clinical_notes", "dla20"]

CPT_CODE_PATTERN = re.compile(r"^\d{5}$")
ICD10_CODE_PATTERN = re.compile(r"^[A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?$")


class ExtractedClaimData(APIModel):
    claim_id: str | None = None
    provider_id: str | None = None
    patient_id: str | None = None
    claim_date: date | None = None
    patient_name: str | None = None
    patient_dob: date | None = None
    provider_name: str | None = None
    provider_license: str | None = None
    provider_npi: str | None = Field(default=None, min_length=10, max_length=10)
    service_dates: list[date] = Field(default_factory=list)
    session_start_time: time | None = None
    session_end_time: time | None = None
    session_duration_minutes: int | None = Field(default=None, ge=0)
    service_location: str | None = None
    cpt_codes: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    place_of_service: str | None = None
    diagnosis_codes: list[str] = Field(default_factory=list)
    billed_units: int | None = Field(default=None, ge=0)
    treatment_plan_date: date | None = None
    authorization_number: str | None = None
    treatment_goals: list[str] = Field(default_factory=list)
    clinical_narrative: str | None = None
    clinical_note_date: date | None = None
    provider_signature_present: bool | None = None
    dla20_deficiency_areas: list[str] = Field(default_factory=list)
    dla20_scores: dict[str, int] = Field(default_factory=dict)
    dla20_total_score: int | None = Field(default=None, ge=0)
    treatment_plan_raw: str | None = None
    clinical_notes_raw: str | None = None
    dla20_raw: str | None = None

    @field_validator("cpt_codes")
    @classmethod
    def validate_cpt_codes(cls, value: list[str]) -> list[str]:
        invalid_codes = [code for code in value if not CPT_CODE_PATTERN.fullmatch(code)]
        if invalid_codes:
            raise ValueError("CPT codes must be 5 digits.")
        return value

    @field_validator("diagnosis_codes")
    @classmethod
    def validate_diagnosis_codes(cls, value: list[str]) -> list[str]:
        invalid_codes = [code for code in value if not ICD10_CODE_PATTERN.fullmatch(code)]
        if invalid_codes:
            raise ValueError("Diagnosis codes must follow basic ICD-10 format.")
        return value

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "claim_id": "CLM-2026-00042",
                    "provider_id": "PRV-1001",
                    "patient_id": "PAT-2002",
                    "claim_date": "2026-06-15",
                    "patient_name": "Jane Doe",
                    "patient_dob": "1988-04-23",
                    "provider_name": "Example Behavioral Health",
                    "provider_license": "LIC-908172",
                    "provider_npi": "1234567890",
                    "service_dates": ["2026-06-12"],
                    "session_start_time": "09:00:00",
                    "session_end_time": "10:00:00",
                    "session_duration_minutes": 60,
                    "service_location": "Outpatient clinic",
                    "cpt_codes": ["90837"],
                    "modifiers": ["GT"],
                    "place_of_service": "11",
                    "diagnosis_codes": ["F41.1"],
                    "billed_units": 1,
                    "treatment_plan_date": "2026-05-30",
                    "authorization_number": "AUTH-7788",
                    "treatment_goals": ["Reduce anxiety symptoms"],
                    "clinical_narrative": "Patient participated in CBT session.",
                    "clinical_note_date": "2026-06-12",
                    "provider_signature_present": True,
                    "dla20_deficiency_areas": ["health_practices"],
                    "dla20_scores": {"health_practices": 4},
                    "dla20_total_score": 52,
                    "treatment_plan_raw": "Treatment plan source text...",
                    "clinical_notes_raw": "Clinical note source text...",
                    "dla20_raw": "DLA-20 source text...",
                }
            ]
        },
    )


class ExtractionRequest(APIModel):
    text: str = Field(min_length=1)
    document_type: DocumentType

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "text": "Claim ID: CLM-2026-00042\nCPT 90837\nDiagnosis F41.1",
                    "document_type": "clinical_notes",
                }
            ]
        },
    )


class ExtractionResponse(APIModel):
    document_type: DocumentType
    extracted_fields: ExtractedClaimData
    confidence: float = Field(ge=0.0, le=1.0)
    provider: str

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "document_type": "clinical_notes",
                    "extracted_fields": {
                        "claim_id": "CLM-2026-00042",
                        "patient_id": "PAT-2002",
                        "claim_date": "2026-06-15",
                        "cpt_codes": ["90837"],
                        "diagnosis_codes": ["F41.1"],
                        "clinical_note_date": "2026-06-12",
                        "provider_signature_present": True,
                    },
                    "confidence": 0.91,
                    "provider": "azure_openai",
                }
            ]
        },
    )
