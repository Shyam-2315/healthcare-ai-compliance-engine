from typing import Any

from app.api.schemas.common import ComplianceFinding
from app.services.rule_engine.registry import get_registered_rules


class ComplianceRuleEngine:
    def validate(
        self,
        claim: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[ComplianceFinding]:
        rule_context = context or {}
        return [rule.evaluate(claim, rule_context) for rule in get_registered_rules()]
