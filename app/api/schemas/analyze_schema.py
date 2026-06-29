from typing import Any

from pydantic import Field

from app.api.schemas.common import APIModel, ComplianceFinding, ComplianceScore
from app.api.schemas.extraction_schema import ExtractionResponse


class AnalyzeRequest(APIModel):
    text: str = Field(min_length=1)
    document_type: str = "claim"
    context: dict[str, Any] = Field(default_factory=dict)


class AnalyzeResponse(APIModel):
    extraction: ExtractionResponse
    findings: list[ComplianceFinding]
    score: ComplianceScore
