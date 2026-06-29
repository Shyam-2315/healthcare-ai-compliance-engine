from typing import Any

from pydantic import ConfigDict, Field

from app.api.schemas.common import APIModel, ComplianceFinding, ComplianceScore
from app.api.schemas.extraction_schema import DocumentType, ExtractionResponse


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
