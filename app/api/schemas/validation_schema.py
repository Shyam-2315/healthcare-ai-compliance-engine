from datetime import date
from typing import Any

from pydantic import ConfigDict, Field

from app.api.schemas.common import APIModel
from app.api.schemas.extraction_schema import ExtractedClaimData
from app.services.rule_engine.base_rule import RedFlagLevel, RulePriority, RuleStatus, ScoreBand


class BhsMatrixEntry(APIModel):
    proc_code: str = Field(min_length=1)
    mod1: str | None = None
    mod2: str | None = None
    mod3: str | None = None
    mod4: str | None = None
    pos_allowed: str | list[str] | None = None
    icd10: str | list[str] | None = None


class CptCredentialEntry(APIModel):
    cpt_code: str = Field(min_length=1)
    license: str | list[str]


class ValidationRequest(APIModel):
    claim_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    patient_id: str = Field(min_length=1)
    claim_date: date
    extracted_data: ExtractedClaimData
    bhs_matrix: list[BhsMatrixEntry] = Field(default_factory=list)
    cpt_credentials: list[CptCredentialEntry] = Field(default_factory=list)
    historical_claims: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "claim_id": "CLAIM-001",
                    "provider_id": "PROV-001",
                    "patient_id": "PAT-001",
                    "claim_date": "2026-06-29",
                    "extracted_data": {
                        "provider_license": "LICSW",
                        "cpt_codes": ["90837"],
                        "modifiers": ["HN"],
                        "place_of_service": "11",
                        "diagnosis_codes": ["F32.1"],
                        "billed_units": 4,
                        "session_start_time": "10:00",
                        "session_end_time": "11:00",
                        "session_duration_minutes": 60,
                        "treatment_plan_date": "2026-01-01",
                        "authorization_number": "AUTH-2026-4451",
                        "provider_signature_present": True,
                        "treatment_goals": ["Reduce depression symptoms"],
                        "clinical_narrative": "Patient worked on depression coping skills and daily functioning goals during the session.",
                        "dla20_deficiency_areas": ["self-care"],
                        "dla20_scores": {"self-care": 2},
                        "dla20_total_score": 2.0,
                        "treatment_plan_raw": "Treatment plan references self-care goals.",
                        "clinical_notes_raw": "Patient worked on depression coping skills.",
                        "dla20_raw": "Self-care: 2",
                    },
                    "bhs_matrix": [
                        {
                            "proc_code": "90837",
                            "mod1": "HN",
                            "pos_allowed": "11,02",
                            "icd10": "F32.1,F41.1",
                        }
                    ],
                    "cpt_credentials": [{"cpt_code": "90837", "license": "LICSW"}],
                    "historical_claims": [],
                }
            ]
        },
    )


class ValidationFlagSummary(APIModel):
    high: int = Field(ge=0)
    medium: int = Field(ge=0)
    low: int = Field(ge=0)


class ValidationRuleResult(APIModel):
    rule_id: str
    rule_name: str
    category: str
    priority: RulePriority
    status: RuleStatus
    message: str
    red_flag_level: RedFlagLevel
    detail: dict[str, Any] = Field(default_factory=dict)


class ValidationResponse(APIModel):
    claim_id: str
    compliance_score: float = Field(ge=0.0, le=100.0)
    score_band: ScoreBand
    passed_rules: list[str]
    failed_rules: list[str]
    flag_summary: ValidationFlagSummary
    results: list[ValidationRuleResult] = Field(min_length=19, max_length=19)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "claim_id": "CLAIM-001",
                    "compliance_score": 92.45,
                    "score_band": "Excellent",
                    "passed_rules": ["TP-001", "TP-002"],
                    "failed_rules": ["CN-001"],
                    "flag_summary": {"high": 0, "medium": 1, "low": 0},
                    "results": [
                        {
                            "rule_id": "TP-001",
                            "rule_name": "Treatment Plan Must Be Current",
                            "category": "Treatment Plan",
                            "priority": "high",
                            "status": "pass",
                            "message": "Treatment plan is current.",
                            "red_flag_level": "none",
                            "detail": {},
                        }
                    ]
                    * 19,
                }
            ]
        },
    )
