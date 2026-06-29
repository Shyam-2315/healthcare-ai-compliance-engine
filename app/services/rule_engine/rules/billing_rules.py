from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class BillingAmountRule(ComplianceRule):
    rule_id = "BIL-001"
    title = "Billing amount is valid"
    severity = "high"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        amount = claim.get("billing_amount") or context.get("billing_amount")
        passed = amount is None or (isinstance(amount, (int, float)) and amount >= 0)
        return self.finding(
            passed=passed,
            message="Billing amount is valid." if passed else "Billing amount is invalid.",
            evidence={"billing_amount": amount},
        )
