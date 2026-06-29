from typing import Any

from pydantic import ConfigDict, Field

from app.api.schemas.common import APIModel, ComplianceFinding, ComplianceScore
from app.api.schemas.extraction_schema import ExtractedClaimData


class ValidationRequest(APIModel):
    claim: ExtractedClaimData
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "claim": {
                        "claim_id": "CLM-2026-00042",
                        "patient_id": "PAT-2002",
                        "claim_date": "2026-06-15",
                        "cpt_codes": ["90837"],
                        "diagnosis_codes": ["F41.1"],
                    },
                    "context": {
                        "provider_credentials": {"1234567890": {"active": True}},
                        "payer_ruleset": "default",
                    },
                }
            ]
        },
    )


class ValidationResponse(APIModel):
    findings: list[ComplianceFinding]
    score: ComplianceScore

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "findings": [
                        {
                            "rule_id": "coding.cpt_required",
                            "title": "CPT code required",
                            "severity": "high",
                            "passed": True,
                            "message": "At least one CPT code is present.",
                            "evidence": {"cpt_codes": ["90837"]},
                        }
                    ],
                    "score": {
                        "compliance_score": 100,
                        "risk_level": "low",
                        "failed_rules": 0,
                        "total_rules": 1,
                    },
                }
            ]
        },
    )
