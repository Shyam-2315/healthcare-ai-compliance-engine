from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class HealthResponse(APIModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "service": "healthcare-compliance-ai",
                    "version": "1.0.0",
                    "environment": "local",
                }
            ]
        },
    )


class ErrorResponse(APIModel):
    error: str
    message: str
    details: dict[str, Any] | None = None

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "error": "validation_error",
                    "message": "Request validation failed.",
                    "details": {
                        "path": "/api/v1/ai/extract",
                        "errors": [
                            {
                                "loc": ["body", "document_type"],
                                "msg": "Input should be 'treatment_plan', 'clinical_notes' or 'dla20'",
                                "type": "literal_error",
                            }
                        ],
                    },
                }
            ]
        },
    )


class ComplianceFinding(APIModel):
    rule_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    passed: bool
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "rule_id": "documentation.clinical_note_present",
                    "title": "Clinical note present",
                    "severity": "high",
                    "passed": False,
                    "message": "A clinical note is required for the billed service date.",
                    "evidence": {"service_date": "2026-06-12"},
                }
            ]
        },
    )


class ComplianceScore(APIModel):
    compliance_score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    failed_rules: int = Field(ge=0)
    total_rules: int = Field(ge=0)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "compliance_score": 86,
                    "risk_level": "medium",
                    "failed_rules": 2,
                    "total_rules": 14,
                }
            ]
        },
    )
