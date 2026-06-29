from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class DocumentationCompletenessRule(ComplianceRule):
    rule_id = "DOC-001"
    title = "Required documentation fields are present"
    severity = "medium"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        required_fields = context.get("required_fields", ["patient_id", "claim_id"])
        missing = [field for field in required_fields if not claim.get(field)]
        return self.finding(
            passed=not missing,
            message=(
                "Required documentation fields are present."
                if not missing
                else "Required documentation fields are missing."
            ),
            evidence={"missing_fields": missing},
        )
