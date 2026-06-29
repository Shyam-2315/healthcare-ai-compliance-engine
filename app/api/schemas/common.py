from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class HealthResponse(APIModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str


class ErrorResponse(APIModel):
    error: str
    message: str
    details: dict[str, Any] | None = None


class ComplianceFinding(APIModel):
    rule_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    passed: bool
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ComplianceScore(APIModel):
    score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    failed_rules: int = Field(ge=0)
    total_rules: int = Field(ge=0)
