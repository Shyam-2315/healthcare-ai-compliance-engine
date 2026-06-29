from typing import Any

from pydantic import Field

from app.api.schemas.common import APIModel, ComplianceFinding, ComplianceScore


class ValidationRequest(APIModel):
    claim: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)


class ValidationResponse(APIModel):
    findings: list[ComplianceFinding]
    score: ComplianceScore
