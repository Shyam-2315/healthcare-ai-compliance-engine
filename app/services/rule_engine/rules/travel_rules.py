from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class TravelDocumentationRule(ComplianceRule):
    rule_id = "TRV-001"
    title = "Travel claim has supporting documentation"
    severity = "medium"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        is_travel_claim = bool(claim.get("travel") or context.get("travel"))
        has_support = bool(claim.get("travel_documentation") or context.get("travel_documentation"))
        passed = not is_travel_claim or has_support
        return self.finding(
            passed=passed,
            message=(
                "Travel documentation requirement is satisfied."
                if passed
                else "Travel claim is missing supporting documentation."
            ),
            evidence={"travel_claim": is_travel_claim, "travel_documentation": has_support},
        )
