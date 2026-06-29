from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field

from app.api.schemas.common import APIModel, ComplianceFinding


class RulePriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RuleStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class RedFlagLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


ScoreBand = Literal["Excellent", "Good", "Fair", "Poor", "Critical"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class RuleResult(APIModel):
    rule_id: str
    rule_name: str
    category: str
    priority: RulePriority
    status: RuleStatus
    message: str
    red_flag_level: RedFlagLevel
    detail: dict[str, Any] = Field(default_factory=dict)


class ValidationOutput(APIModel):
    results: list[RuleResult]
    passed_rules: list[RuleResult]
    failed_rules: list[RuleResult]
    compliance_score: float = Field(ge=0.0, le=100.0)
    score_band: ScoreBand
    risk_level: RiskLevel
    high_red_flags: int = Field(ge=0)
    medium_red_flags: int = Field(ge=0)
    low_red_flags: int = Field(ge=0)
    total_rules: int = Field(ge=0)


class BaseRule(ABC):
    rule_id: str
    rule_name: str
    category: str
    priority: RulePriority

    @abstractmethod
    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        raise NotImplementedError

    def _pass(self, message: str, detail: dict[str, Any] | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            priority=self.priority,
            status=RuleStatus.PASS,
            message=message,
            red_flag_level=RedFlagLevel.NONE,
            detail=detail or {},
        )

    def _fail(
        self,
        message: str,
        red_flag: RedFlagLevel,
        detail: dict[str, Any] | None = None,
    ) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            priority=self.priority,
            status=RuleStatus.FAIL,
            message=message,
            red_flag_level=red_flag,
            detail=detail or {},
        )


Severity = Literal["low", "medium", "high", "critical"]


class ComplianceRule(ABC):
    """Compatibility base for pre-Phase 6 placeholder rules."""

    rule_id: str
    title: str
    severity: Severity

    @abstractmethod
    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]) -> ComplianceFinding:
        raise NotImplementedError

    def finding(
        self,
        *,
        passed: bool,
        message: str,
        evidence: dict[str, Any] | None = None,
    ) -> ComplianceFinding:
        return ComplianceFinding(
            rule_id=self.rule_id,
            title=self.title,
            severity=self.severity,
            passed=passed,
            message=message,
            evidence=evidence or {},
        )
