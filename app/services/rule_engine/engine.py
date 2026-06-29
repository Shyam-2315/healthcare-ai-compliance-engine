from typing import Any

from app.api.schemas.common import ComplianceFinding
from app.services.rule_engine.base_rule import (
    BaseRule,
    RedFlagLevel,
    RulePriority,
    RuleResult,
    RuleStatus,
    ValidationOutput,
)
from app.services.rule_engine.registry import get_registered_rules
from app.services.rule_engine.scoring import ComplianceScoringEngine


class RuleEngine:
    def __init__(self, rules: list[BaseRule]) -> None:
        self._rules = rules
        self._scoring_engine = ComplianceScoringEngine()

    def run(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> ValidationOutput:
        results: list[RuleResult] = []
        for rule in self._rules:
            try:
                results.append(
                    rule.evaluate(
                        extracted,
                        bhs_matrix,
                        cpt_credentials,
                        historical_claims,
                    )
                )
            except Exception as exc:
                results.append(self._crash_result(rule, exc))

        passed_rules = [result for result in results if result.status == RuleStatus.PASS]
        failed_rules = [result for result in results if result.status == RuleStatus.FAIL]
        compliance_score = self._scoring_engine.calculate_score(results)

        return ValidationOutput(
            results=results,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            compliance_score=compliance_score,
            score_band=self._scoring_engine.score_band(compliance_score),
            risk_level=self._scoring_engine.risk_level(compliance_score),
            high_red_flags=self._count_red_flags(results, RedFlagLevel.HIGH),
            medium_red_flags=self._count_red_flags(results, RedFlagLevel.MEDIUM),
            low_red_flags=self._count_red_flags(results, RedFlagLevel.LOW),
            total_rules=len(results),
        )

    @staticmethod
    def _count_red_flags(results: list[RuleResult], level: RedFlagLevel) -> int:
        return sum(1 for result in results if result.red_flag_level == level)

    @staticmethod
    def _crash_result(rule: BaseRule, exc: Exception) -> RuleResult:
        return RuleResult(
            rule_id=rule.rule_id,
            rule_name=rule.rule_name,
            category=rule.category,
            priority=rule.priority,
            status=RuleStatus.FAIL,
            message=f"Rule execution failed: {exc}",
            red_flag_level=RuleEngine._red_flag_for_priority(rule.priority),
            detail={"exception_type": type(exc).__name__},
        )

    @staticmethod
    def _red_flag_for_priority(priority: RulePriority) -> RedFlagLevel:
        if priority == RulePriority.HIGH:
            return RedFlagLevel.HIGH
        if priority == RulePriority.MEDIUM:
            return RedFlagLevel.MEDIUM
        return RedFlagLevel.LOW


class ComplianceRuleEngine:
    """Compatibility facade for current validation routes."""

    def validate(
        self,
        claim: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[ComplianceFinding]:
        rule_context = context or {}
        findings: list[ComplianceFinding] = []
        for rule in get_registered_rules():
            try:
                findings.append(rule.evaluate(claim, rule_context))
            except Exception as exc:
                findings.append(
                    ComplianceFinding(
                        rule_id=getattr(rule, "rule_id", "unknown"),
                        title=getattr(rule, "title", "Rule execution failed"),
                        severity=getattr(rule, "severity", "critical"),
                        passed=False,
                        message=f"Rule execution failed: {exc}",
                        evidence={"exception_type": type(exc).__name__},
                    )
                )
        return findings
