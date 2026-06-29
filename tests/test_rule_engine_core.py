from typing import Any

from app.services.rule_engine.base_rule import (
    BaseRule,
    RedFlagLevel,
    RulePriority,
    RuleResult,
    RuleStatus,
)
from app.services.rule_engine.engine import RuleEngine
from app.services.rule_engine.registry import get_rule_count, validate_rule_registry


class DummyPassRule(BaseRule):
    rule_id = "PASS-001"
    rule_name = "Dummy pass rule"
    category = "test"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        return self._pass("Passed.", {"claim_id": extracted.get("claim_id")})


class DummyFailRule(BaseRule):
    rule_id = "FAIL-001"
    rule_name = "Dummy fail rule"
    category = "test"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        return self._fail("Failed.", RedFlagLevel.HIGH, {"reason": "missing"})


class DummyCrashRule(BaseRule):
    rule_id = "CRASH-001"
    rule_name = "Dummy crash rule"
    category = "test"
    priority = RulePriority.LOW

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        raise RuntimeError("boom")


def test_dummy_pass_rule_works() -> None:
    result = DummyPassRule().evaluate({"claim_id": "CLAIM-001"}, {}, {}, [])

    assert result.status == RuleStatus.PASS
    assert result.red_flag_level == RedFlagLevel.NONE
    assert result.detail == {"claim_id": "CLAIM-001"}


def test_dummy_fail_rule_works() -> None:
    result = DummyFailRule().evaluate({}, {}, {}, [])

    assert result.status == RuleStatus.FAIL
    assert result.red_flag_level == RedFlagLevel.HIGH


def test_rule_engine_continues_if_one_rule_crashes() -> None:
    output = RuleEngine([DummyPassRule(), DummyCrashRule(), DummyFailRule()]).run(
        {"claim_id": "CLAIM-001"},
        {},
        {},
        [],
    )

    assert [result.rule_id for result in output.results] == ["PASS-001", "CRASH-001", "FAIL-001"]
    assert len(output.passed_rules) == 1
    assert len(output.failed_rules) == 2
    assert output.failed_rules[0].message == "Rule execution failed: boom"


def test_rule_engine_flag_counts_are_correct() -> None:
    output = RuleEngine([DummyFailRule(), DummyCrashRule()]).run({}, {}, {}, [])

    assert output.high_red_flags == 1
    assert output.medium_red_flags == 0
    assert output.low_red_flags == 1
    assert output.total_rules == 2


def test_empty_phase5_registry_is_valid() -> None:
    assert get_rule_count() == 0
    assert validate_rule_registry() is True
