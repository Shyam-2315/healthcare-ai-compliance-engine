from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class CredentialRule(ComplianceRule):
    rule_id = "CRD-001"
    title = "Provider credential is valid"
    severity = "critical"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        provider_id = claim.get("provider_id")
        valid_provider_ids = set(context.get("valid_provider_ids", []))
        passed = not valid_provider_ids or provider_id in valid_provider_ids
        return self.finding(
            passed=passed,
            message=(
                "Provider credential is valid."
                if passed
                else "Provider credential could not be verified."
            ),
            evidence={"provider_id": provider_id},
        )
