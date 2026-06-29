from abc import ABC, abstractmethod
from typing import Any, Literal

from app.api.schemas.common import ComplianceFinding

Severity = Literal["low", "medium", "high", "critical"]


class ComplianceRule(ABC):
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
