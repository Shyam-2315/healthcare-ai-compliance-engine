from typing import Literal

from app.api.schemas.common import ComplianceFinding, ComplianceScore

RiskLevel = Literal["low", "medium", "high", "critical"]


class ComplianceScorer:
    _severity_weights = {
        "low": 5,
        "medium": 10,
        "high": 20,
        "critical": 35,
    }

    def score(self, findings: list[ComplianceFinding]) -> ComplianceScore:
        failed_findings = [finding for finding in findings if not finding.passed]
        penalty = sum(self._severity_weights[finding.severity] for finding in failed_findings)
        score = max(0, 100 - penalty)
        return ComplianceScore(
            compliance_score=score,
            risk_level=self._risk_level(score),
            failed_rules=len(failed_findings),
            total_rules=len(findings),
        )

    @staticmethod
    def _risk_level(score: int) -> RiskLevel:
        if score >= 90:
            return "low"
        if score >= 75:
            return "medium"
        if score >= 50:
            return "high"
        return "critical"
