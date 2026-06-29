from typing import Any, Literal

from pydantic import ConfigDict, Field

from app.api.schemas.common import APIModel, ComplianceFinding, ComplianceScore
from app.api.schemas.extraction_schema import DocumentType, ExtractedClaimData, ExtractionResponse
from app.api.schemas.validation_schema import ValidationFlagSummary, ValidationRuleResult
from app.services.rule_engine.base_rule import ScoreBand


class AnalyzeRequest(APIModel):
    text: str = Field(min_length=1)
    document_type: DocumentType
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "text": "Claim ID: CLM-2026-00042\nCPT 90837\nDiagnosis F41.1",
                    "document_type": "clinical_notes",
                    "context": {"payer_ruleset": "default"},
                }
            ]
        },
    )


class AnalyzeResponse(APIModel):
    extraction: ExtractionResponse
    findings: list[ComplianceFinding]
    score: ComplianceScore

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "extraction": {
                        "document_type": "clinical_notes",
                        "extracted_fields": {
                            "claim_id": "CLM-2026-00042",
                            "patient_id": "PAT-2002",
                            "claim_date": "2026-06-15",
                            "cpt_codes": ["90837"],
                            "diagnosis_codes": ["F41.1"],
                        },
                        "confidence": 0.91,
                        "provider": "azure_openai",
                    },
                    "findings": [],
                    "score": {
                        "compliance_score": 100,
                        "risk_level": "low",
                        "failed_rules": 0,
                        "total_rules": 0,
                    },
                }
            ]
        },
    )


class AnalyzeClaimOCRSummary(APIModel):
    total_documents: int = Field(ge=0)
    treatment_plan_documents: int = Field(ge=0)
    clinical_note_documents: int = Field(ge=0)
    dla20_documents: int = Field(ge=0)


class AnalyzeClaimMetadata(APIModel):
    processing_time_ms: int = Field(ge=0)
    rules_executed: int = Field(ge=0)
    ocr_documents_processed: int = Field(ge=0)


class AnalyzeClaimResponse(APIModel):
    claim_id: str
    ai_status: Literal["validated"]
    compliance_score: float = Field(ge=0.0, le=100.0)
    score_band: ScoreBand
    ocr_summary: AnalyzeClaimOCRSummary
    extracted_data: ExtractedClaimData
    flag_summary: ValidationFlagSummary
    rule_results: list[ValidationRuleResult] = Field(min_length=19, max_length=19)
    metadata: AnalyzeClaimMetadata

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "claim_id": "CLAIM-001",
                    "ai_status": "validated",
                    "compliance_score": 92.45,
                    "score_band": "Excellent",
                    "ocr_summary": {
                        "total_documents": 3,
                        "treatment_plan_documents": 1,
                        "clinical_note_documents": 1,
                        "dla20_documents": 1,
                    },
                    "extracted_data": {
                        "claim_id": "CLAIM-001",
                        "provider_id": "PROV-001",
                        "patient_id": "PAT-001",
                        "claim_date": "2026-06-29",
                        "cpt_codes": ["90837"],
                    },
                    "flag_summary": {"high": 0, "medium": 1, "low": 0},
                    "rule_results": [
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
                    "metadata": {
                        "processing_time_ms": 1234,
                        "rules_executed": 19,
                        "ocr_documents_processed": 3,
                    },
                }
            ]
        },
    )
