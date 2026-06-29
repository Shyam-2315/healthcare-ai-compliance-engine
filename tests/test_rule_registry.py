from app.services.rule_engine.base_rule import RulePriority
from app.services.rule_engine.registry import get_all_rules, get_rule_count, validate_rule_registry

EXPECTED_PRIORITIES = {
    "TP-001": RulePriority.HIGH,
    "TP-002": RulePriority.HIGH,
    "TP-003": RulePriority.HIGH,
    "CPT-001": RulePriority.HIGH,
    "MOD-001": RulePriority.MEDIUM,
    "POS-001": RulePriority.HIGH,
    "DX-001": RulePriority.HIGH,
    "DUR-001": RulePriority.HIGH,
    "UNIT-001": RulePriority.MEDIUM,
    "TOVL-001": RulePriority.HIGH,
    "CN-001": RulePriority.MEDIUM,
    "SIG-001": RulePriority.MEDIUM,
    "CQ-001": RulePriority.LOW,
    "CRED-001": RulePriority.HIGH,
    "TRV-001": RulePriority.LOW,
    "DLA-001": RulePriority.MEDIUM,
    "DLA-002": RulePriority.MEDIUM,
    "FRD-001": RulePriority.HIGH,
    "FRD-002": RulePriority.HIGH,
}


def test_get_all_rules_returns_exactly_19_rules() -> None:
    rules = get_all_rules()

    assert len(rules) == 19
    assert get_rule_count() == 19


def test_all_rule_ids_are_unique() -> None:
    rule_ids = [rule.rule_id for rule in get_all_rules()]

    assert len(rule_ids) == len(set(rule_ids))


def test_rule_priorities_are_correct() -> None:
    assert {rule.rule_id: rule.priority for rule in get_all_rules()} == EXPECTED_PRIORITIES


def test_rule_registry_is_valid() -> None:
    assert validate_rule_registry() is True
