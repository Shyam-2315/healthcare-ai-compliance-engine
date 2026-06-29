from app.services.rule_engine.base_rule import BaseRule, ComplianceRule


def get_all_rules() -> list[BaseRule]:
    return []


def get_rule_count() -> int:
    return len(get_all_rules())


def validate_rule_registry() -> bool:
    rule_ids = [rule.rule_id for rule in get_all_rules()]
    return len(rule_ids) == len(set(rule_ids))


def get_registered_rules() -> list[ComplianceRule]:
    """Compatibility registry for current validation routes until Phase 6 rules land."""

    return []
