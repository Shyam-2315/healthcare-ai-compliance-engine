import pytest

from app.services.rule_engine.base_rule import RedFlagLevel, RulePriority, RuleResult, RuleStatus
from app.services.rule_engine.registry import get_all_rules
from app.services.rule_engine.scoring import ComplianceScoringEngine


def _result(rule_id: str, priority: RulePriority, status: RuleStatus) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Rule {rule_id}",
        category="test",
        priority=priority,
        status=status,
        message="done",
        red_flag_level=RedFlagLevel.NONE if status == RuleStatus.PASS else RedFlagLevel.HIGH,
        detail={},
    )


def test_scoring_all_pass_returns_100() -> None:
    score = ComplianceScoringEngine().calculate_score(
        [
            _result("R1", RulePriority.HIGH, RuleStatus.PASS),
            _result("R2", RulePriority.MEDIUM, RuleStatus.PASS),
            _result("R3", RulePriority.LOW, RuleStatus.PASS),
        ]
    )

    assert score == 100.0


def test_scoring_high_priority_fail_reduces_score_correctly() -> None:
    score = ComplianceScoringEngine().calculate_score(
        [
            _result("R1", RulePriority.HIGH, RuleStatus.FAIL),
            _result("R2", RulePriority.MEDIUM, RuleStatus.PASS),
            _result("R3", RulePriority.LOW, RuleStatus.PASS),
        ]
    )

    assert score == 48.15


def test_scoring_empty_rule_list_returns_zero() -> None:
    assert ComplianceScoringEngine().calculate_score([]) == 0.0


@pytest.mark.parametrize(
    ("score", "band"),
    [(100.0, "Excellent"), (89.99, "Good"), (74.99, "Fair"), (49.99, "Poor"), (24.99, "Critical")],
)
def test_score_band_logic(score: float, band: str) -> None:
    assert ComplianceScoringEngine.score_band(score) == band


@pytest.mark.parametrize(
    ("score", "risk_level"),
    [(100.0, "low"), (89.99, "medium"), (74.99, "high"), (49.99, "critical")],
)
def test_risk_level_logic(score: float, risk_level: str) -> None:
    assert ComplianceScoringEngine.risk_level(score) == risk_level


def test_total_scoring_weight_is_106() -> None:
    weights = {
        RulePriority.HIGH: 7.0,
        RulePriority.MEDIUM: 4.0,
        RulePriority.LOW: 2.5,
    }

    total_weight = sum(weights[rule.priority] for rule in get_all_rules())

    assert total_weight == 106.0
