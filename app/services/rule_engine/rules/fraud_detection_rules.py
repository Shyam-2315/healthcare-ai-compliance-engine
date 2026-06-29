from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class DuplicateClaimRule(ComplianceRule):
    rule_id = "FRD-001"
    title = "Duplicate claim risk"
    severity = "critical"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        claim_id = claim.get("claim_id")
        historical_claim_ids = set(context.get("historical_claim_ids", []))
        duplicate = bool(claim_id and claim_id in historical_claim_ids)
        return self.finding(
            passed=not duplicate,
            message=(
                "No duplicate claim risk detected."
                if not duplicate
                else "Claim appears to duplicate a historical claim."
            ),
            evidence={"claim_id": claim_id, "duplicate": duplicate},
        )
