from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class DLA20DocumentationRule(ComplianceRule):
    rule_id = "DLA20-001"
    title = "DLA-20 score is documented when required"
    severity = "medium"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        required = bool(context.get("requires_dla20"))
        dla20_score = claim.get("dla20_score") or context.get("dla20_score")
        passed = not required or dla20_score is not None
        return self.finding(
            passed=passed,
            message=(
                "DLA-20 documentation requirement is satisfied."
                if passed
                else "DLA-20 score is required but missing."
            ),
            evidence={"requires_dla20": required, "dla20_score": dla20_score},
        )
