from app.api.schemas.common import ComplianceFinding, ComplianceScore
from app.services.rule_engine.base_rule import (
    RiskLevel,
    RulePriority,
    RuleResult,
    RuleStatus,
    ScoreBand,
)


class ComplianceScoringEngine:
    _priority_weights: dict[RulePriority, float] = {
        RulePriority.HIGH: 7.0,
        RulePriority.MEDIUM: 4.0,
        RulePriority.LOW: 2.5,
    }

    def calculate_score(self, results: list[RuleResult]) -> float:
        total_active_rule_weight = sum(self._priority_weights[result.priority] for result in results)
        if total_active_rule_weight == 0:
            return 0.0

        passed_rule_weight = sum(
            self._priority_weights[result.priority]
            for result in results
            if result.status == RuleStatus.PASS
        )
        return round((passed_rule_weight / total_active_rule_weight) * 100, 2)

    @staticmethod
    def score_band(score: float) -> ScoreBand:
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 50:
            return "Fair"
        if score >= 25:
            return "Poor"
        return "Critical"

    @staticmethod
    def risk_level(score: float) -> RiskLevel:
        if score >= 90:
            return "low"
        if score >= 75:
            return "medium"
        if score >= 50:
            return "high"
        return "critical"


class ComplianceScorer:
    """Compatibility scorer for current API response schemas."""

    _severity_weights = {
        "low": 5,
        "medium": 10,
        "high": 20,
        "critical": 35,
    }

    def score(self, findings: list[ComplianceFinding]) -> ComplianceScore:
        failed_findings = [finding for finding in findings if not finding.passed]
        penalty = sum(self._severity_weights[finding.severity] for finding in failed_findings)
        compliance_score = max(0, 100 - penalty)
        return ComplianceScore(
            compliance_score=compliance_score,
            risk_level=ComplianceScoringEngine.risk_level(float(compliance_score)),
            failed_rules=len(failed_findings),
            total_rules=len(findings),
        )
